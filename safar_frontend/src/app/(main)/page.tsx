import { HeaderFilters } from "@/components/layout/header/header-filters";
import { MSearch } from "@/components/layout/header/Serch";
import { ListBox } from "@/components/main/box/box-list";
import { ListExperience } from "@/components/main/experience/experience-list";
import { ListPlaces } from "@/components/main/place/place-list";


export default function Home() {
  return (
    <div>
      <MSearch/>
      <div className="sticky top-0 z-10 bg-background/50 backdrop-blur-lg items-center justify-center ">
      <HeaderFilters/>
      </div>
      <div className="px-2 sm:px-6 lg:px-8 md:mx-8 space-y-4">
        <h2 className="text-2xl font-bold my-4 ">picked for you Box</h2>
        <ListBox overlay={false} loop={true} />
        <h2 className="text-2xl font-bold my-4">Featured Experiences</h2>
        <ListExperience overlay={true} loop={true} />
        <h2 className="text-2xl font-bold my-4">Most popular Places</h2>
        <ListPlaces overlay={true} />
        </div>
    </div>
  )
}

