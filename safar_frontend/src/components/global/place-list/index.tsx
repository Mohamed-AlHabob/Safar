"use client"

import { useState } from "react"
import { useGetPlacesQuery } from "@/redux/services/api"
import { Button } from "@/components/ui/button"
import { PlaceCard } from "./place-card"
import { Spinner } from "@/components/ui/spinner"
import { Place } from "@/redux/types/types"

type Props = {
  overlay?: boolean
  selected?: string
  favorites?: string[]
  onFavoriteToggle?: (id: string) => void
}

export const ListPlaces = ({ selected, favorites = [], onFavoriteToggle }: Props) => {
  const [page, setPage] = useState(1)
  const [allFetchedPlaces, setAllFetchedPlaces] = useState<Place[]>([])

  const { data, isLoading, isFetching, error } = useGetPlacesQuery({page,page_size: 12})
  
  if (data?.results && !isFetching) {
    const newPlaces = data.results.filter(
      newPlace => !allFetchedPlaces.some(place => place.id === newPlace.id)
    )
    if (newPlaces.length > 0) {
      setAllFetchedPlaces(prev => [...prev, ...newPlaces])
    }
  }

  const handleLoadMore = () => {
    if (!isFetching) {
      setPage(prev => prev + 1)
    }
  }

  const hasMorePlaces = data?.next !== null
  
  const isPlaceFavorited = (placeId: string) => {
    return favorites.includes(placeId)
  }

  const handleFavorite = (id: string) => {
    if (onFavoriteToggle) {
      onFavoriteToggle(id)
    }
  }

  if (error) {
    return (
      <div className="flex justify-center items-center p-8 text-red-500">
        <p>Error loading places. Please try again later.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-full mt-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-12 w-full overflow-x-auto pb-4">
      {allFetchedPlaces.length > 0 ? (
          allFetchedPlaces.map((place) => (
            <div
              key={place.id}
              className={`transition-all duration-200 ${
                selected === place.id ? "scale-[1.02] ring-2 ring-primary ring-offset-2 rounded-3xl" : ""
              }`}
            >
                <PlaceCard 
                  place={place} 
                  onFavorite={handleFavorite} 
                  isFavorited={isPlaceFavorited(place.id)} 
                />
            </div>
          ))
        ) : !isLoading ? (
          <div className="flex justify-center items-center p-8 text-gray-500 col-span-full">
            <p>No places found.</p>
          </div>
        ) : null}

        {isLoading && isFetching && (
          <div className="flex justify-center p-6 col-span-full">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-12 w-full overflow-x-auto pb-4">
            <PlaceCard.Skeleton />
            <PlaceCard.Skeleton />
            <PlaceCard.Skeleton />
            <PlaceCard.Skeleton />
            </div>
          </div>
        )}
      </div>

      {/* Load more button */}
      {hasMorePlaces && (
        <div className="my-8 w-full flex justify-center">
          <Button 
            onClick={handleLoadMore} 
            disabled={isFetching} 
            className="px-8" 
            variant="outline"
          >
            {isFetching ? (
              <>
                <Spinner className="mr-2 h-4 w-4" />
              </>
            ) : (
              "More"
            )}
          </Button>
        </div>
      )}
    </div>
  )
}
