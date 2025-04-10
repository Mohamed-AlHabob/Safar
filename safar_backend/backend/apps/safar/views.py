from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils import timezone
from apps.core_apps.general import GENPagination
from apps.safar.models import (
    Category, Discount, Place, Experience,
    Flight, Box, Booking, Wishlist, Review, Payment, Message, Notification
)
from apps.core_apps.generation_algorithm import BoxGenerator
from apps.safar.serializers import (
    CategorySerializer,
    DiscountSerializer, PlaceSerializer, ExperienceSerializer, FlightSerializer,
    BoxSerializer, BookingSerializer, WishlistSerializer, ReviewSerializer,
    PaymentSerializer, MessageSerializer, NotificationSerializer
)

class BaseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] 
    pagination_class = GENPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.queryset.model, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)
        return queryset

class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class DiscountViewSet(BaseViewSet):
    queryset = Discount.objects.all().prefetch_related(
        'applicable_places',
        'applicable_experiences',
        'applicable_flights',
        'applicable_boxes'
    )
    serializer_class = DiscountSerializer
    filterset_fields = ['discount_type', 'is_active']
    search_fields = ['code']
    ordering_fields = ['valid_from', 'valid_to', 'amount']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active discounts"""
        now = timezone.now()
        discounts = self.get_queryset().filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
        serializer = self.get_serializer(discounts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply discount to a booking"""
        discount = self.get_object()
        booking_id = request.data.get('booking_id')
        # discount application logic
        return Response({'status': 'Discount applied'})

class PlaceViewSet(BaseViewSet):
    queryset = Place.objects.select_related(
        'category', 'country', 'city', 'region', 'owner'
    ).prefetch_related('media')
    serializer_class = PlaceSerializer
    filterset_fields = ['category', 'country', 'city', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['rating', 'price', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Enhanced search that also generates personalized boxes
        """
        query = request.query_params.get('q', '')
        location = request.query_params.get('location')
        
        # Convert location if provided
        geo_location = None
        if location:
            try:
                geo_location = GEOSGeometry(location)
            except:
                pass
        
        places = self.filter_queryset(self.get_queryset())
        places = self.paginate_queryset(places)
        serializer = self.get_serializer(places, many=True)
        
        box = None
        if request.user.is_authenticated:
            generator = BoxGenerator(
                user=request.user,
                search_query=query,
                location=geo_location
            )
            box = generator.generate_personalized_box()
        
        response_data = {
            'results': serializer.data,
            'personalized_box': BoxSerializer(box).data if box else None
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Get similar places"""
        place = self.get_object()
        similar_places = self.get_queryset().filter(
            category=place.category
        ).exclude(id=place.id)[:5]
        serializer = self.get_serializer(similar_places, many=True)
        return Response(serializer.data)

class ExperienceViewSet(BaseViewSet):
    queryset = Experience.objects.select_related(
        'place', 'owner'
    ).prefetch_related('media')
    serializer_class = ExperienceSerializer
    filterset_fields = ['place', 'is_available']
    search_fields = ['title', 'description']
    ordering_fields = ['rating', 'price_per_person', 'duration']
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check availability for specific dates"""
        experience = self.get_object()
        date = request.query_params.get('date')
        # Add availability checking logic
        return Response({'available': True, 'capacity': experience.capacity})

class FlightViewSet(BaseViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    filterset_fields = ['airline', 'departure_airport', 'arrival_airport']
    search_fields = ['flight_number', 'arrival_city']
    ordering_fields = ['departure_time', 'arrival_time', 'price']
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search flights with filters"""
        departure = request.query_params.get('departure')
        arrival = request.query_params.get('arrival')
        date = request.query_params.get('date')
        
        queryset = self.get_queryset()
        if departure:
            queryset = queryset.filter(departure_airport=departure)
        if arrival:
            queryset = queryset.filter(arrival_airport=arrival)
        if date:
            queryset = queryset.filter(departure_time__date=date)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BoxViewSet(BaseViewSet):
    queryset = Box.objects.select_related('country', 'city').prefetch_related('media')
    serializer_class = BoxSerializer
    filterset_fields = ['country', 'city']
    search_fields = ['name', 'description']
    ordering_fields = ['total_price', 'created_at']

    @action(detail=False, methods=['post'], url_path='test-generator')
    def test_generator(self, request):
        """
        Custom endpoint to test BoxGenerator functionality
        
        Parameters:
        - location (optional): "lat,lng" string
        - search_query (optional): search query
        - debug (optional): boolean to return debug info
        
        Returns:
        - Generated box
        - Status
        """
        
        location = request.data.get('location')
        search_query = request.data.get('search_query', '')
        debug = request.data.get('debug', False)

        geo_location = None
        if location:
            try:
                lat, lng = map(float, location.split(','))
                geo_location = Point(lng, lat)
            except:
                return Response(
                    {'error': 'Invalid location format. Use "lat,lng"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            generator = BoxGenerator(
                user=request.user,
                location=geo_location,
                search_query=search_query
            )
            
            box = generator.generate_personalized_box()
            
            response_data = {
                'status': 'success',
                'box': BoxSerializer(box).data if box else None,
                'generated_at': timezone.now().isoformat()
            }
            
            if debug:
                response_data['debug'] = {
                    'user_cluster': generator.user_cluster,
                    'trending_destinations': generator.trending_destinations,
                    'search_results': generator.search_results,
                    'generation_time': generator.generation_time
                }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': str(e), 'status': 'failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='test-generator-bulk')
    def test_generator_bulk(self, request):
        """
        Generate multiple test boxes with different parameters
        
        Parameters:
        - locations: list of "lat,lng" strings
        - queries: list of search queries
        - count: number of boxes to generate per combination
        
        Returns:
        - Generated boxes
        - Status
        """
        
        locations = request.data.get('locations', [])
        queries = request.data.get('queries', [])
        count = int(request.data.get('count', 1))
        
        results = []
        for loc in locations:
            for q in queries:
                try:

                    geo_location = None
                    if loc:
                        try:
                            lat, lng = map(float, loc.split(','))
                            geo_location = Point(lng, lat)
                        except:
                            continue
                    
                    for i in range(count):
                        generator = BoxGenerator(
                            user=request.user,
                            location=geo_location,
                            search_query=q
                        )
                        
                        box = generator.generate_personalized_box()
                        results.append({
                            'location': loc,
                            'query': q,
                            'box': BoxSerializer(box).data if box else None,
                            'success': box is not None
                        })
                        
                except Exception as e:
                    results.append({
                        'location': loc,
                        'query': q,
                        'error': str(e),
                        'success': False
                    })
        
        return Response({
            'results': results,
            'generated_at': timezone.now().isoformat()
        })

    @action(detail=False, methods=['get'], url_path='test-generator-defaults')
    def test_generator_defaults(self, request):
        """
        Generate test boxes with default parameters
        
        Returns:
        - Generated boxes
        - Status
        """
        scenarios = [
            {'name': 'Default', 'params': {}},
            {'name': 'Beach', 'params': {'search_query': 'beach vacation'}},
            {'name': 'Mountain', 'params': {'search_query': 'mountain retreat'}},
            {'name': 'City', 'params': {'search_query': 'city break'}}
        ]
        
        results = []
        for scenario in scenarios:
            try:
                generator = BoxGenerator(
                    user=request.user,
                    **scenario['params']
                )
                
                box = generator.generate_personalized_box()
                results.append({
                    'scenario': scenario['name'],
                    'box': BoxSerializer(box).data if box else None,
                    'success': box is not None
                })
                
            except Exception as e:
                results.append({
                    'scenario': scenario['name'],
                    'error': str(e),
                    'success': False
                })
        
        return Response({
            'results': results,
            'generated_at': timezone.now().isoformat()
        })

    @action(detail=True, methods=['get'])
    def itinerary(self, request, pk=None):
        """Get detailed itinerary for a box"""
        box = self.get_object()
        return Response({'itinerary': 'Detailed itinerary would be here'})

class BookingViewSet(BaseViewSet):
    queryset = Booking.objects.select_related(
        'user', 'place', 'experience', 'flight', 'box'
    )
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'payment_status']
    ordering_fields = ['booking_date', 'check_in', 'check_out']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to confirm this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'Confirmed'
        booking.save()
        return Response({'status': 'Booking confirmed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'Cancelled'
        booking.save()
        return Response({'status': 'Booking cancelled'})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get user's upcoming bookings"""
        bookings = self.get_queryset().filter(
            user=request.user,
            check_out__gte=timezone.now(),
            status='Confirmed'
        ).order_by('check_in')
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

class WishlistViewSet(BaseViewSet):
    queryset = Wishlist.objects.select_related(
        'user', 'place', 'experience', 'flight', 'box'
    )
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def mine(self, request):
        """Get current user's wishlist"""
        wishlist = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(wishlist, many=True)
        return Response(serializer.data)

class ReviewViewSet(BaseViewSet):
    queryset = Review.objects.select_related(
        'user', 'place', 'experience', 'flight'
    )
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['rating']
    ordering_fields = ['rating', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

class PaymentViewSet(BaseViewSet):
    queryset = Payment.objects.select_related('user', 'booking')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['payment_status']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Mark payment as paid (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admin can mark payments as paid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment = self.get_object()
        payment.payment_status = 'Paid'
        payment.save()
        return Response({'status': 'Payment marked as paid'})

class MessageViewSet(BaseViewSet):
    queryset = Message.objects.select_related('sender', 'receiver', 'booking')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
            )
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        if message.receiver != request.user:
            return Response(
                {'error': 'You can only mark your own messages as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message.save()
        return Response({'status': 'Message marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages for current user"""
        messages = self.get_queryset().filter(
            receiver=request.user,
            is_read=False
        )
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class NotificationViewSet(BaseViewSet):
    queryset = Notification.objects.select_related('user')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        if notification.user != request.user:
            return Response(
                {'error': 'You can only mark your own notifications as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications for current user"""
        notifications = self.get_queryset().filter(
            user=request.user,
            is_read=False
        )
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'status': f'{updated} notifications marked as read'})



