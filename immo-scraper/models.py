from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Optional


@dataclass
class Listing:
    id: str
    publish_date: datetime
    title: str
    url: str
    address: str
    price_cold: int
    price_warm: int
    size: int
    rooms: float

    def to_text(self) -> str:
        # Start with the title on the first line
        text = f"Title: {self.title}\n"

        # Add all attributes as key-value pairs
        text += f"ID: {self.id}\n"
        text += f"Publish Date: {self.publish_date}\n"
        text += f"URL: {self.url}\n"
        text += f"Address: {self.address}\n"
        text += f"Price Cold: {self.price_cold}\n"
        text += f"Price Warm: {self.price_warm}\n"
        text += f"Size: {self.size}\n"
        text += f"Rooms: {self.rooms}\n"

        return text


@dataclass
class Filter:
    price_cold: Optional[int]
    price_warm: Optional[int]
    min_size: Optional[int]
    min_rooms: Optional[float]
    last_checked: Optional[datetime]
    def match(self, listing: Listing) -> bool:
        res = True
        res &= not self.price_cold or self.price_cold >= listing.price_cold
        res &= not self.price_warm or self.price_warm >= listing.price_warm
        res &= not self.min_size or self.min_size <= listing.size
        res &= not self.min_rooms or self.min_rooms <= listing.rooms
        res &= not self.last_checked or self.last_checked <= listing.publish_date

        return res


def parse_listing(listing: json) -> Listing:
    inner = listing["resultlist.realEstate"]
    addr = inner["address"]
    publish_date = datetime.fromisoformat(listing["@publishDate"])
    id = inner["@id"]
    url = f"https://www.immobilienscout24.de/expose/{id}"
    title = inner["title"]

    address = f"{addr.get("street", "UNKOWN")} {addr.get("houseNumber", "UNKNOWN")}, {addr["postcode"]} {addr["city"]} - {addr["quarter"]}"
    price_cold = inner["price"]["value"]
    price_warm = inner["calculatedTotalRent"]["totalRent"]["value"]
    size = inner["livingSpace"]
    rooms = inner["numberOfRooms"]

    return Listing(
        id=id,
        url=url,
        publish_date=publish_date,
        title=title,
        address=address,
        price_cold=price_cold,
        price_warm=price_warm,
        size=size,
        rooms=rooms,
    )


def parse_listings(listing_resp: json) -> List[Listing]:
    return list(
        map(
            parse_listing,
            listing_resp["searchResponseModel"]["resultlist.resultlist"][
                "resultlistEntries"
            ][0]["resultlistEntry"],
        )
    )
