building a bmw finder app that finds cars directly from the dealership websites 

docker compose up --build always works, exposed on port 9292

use the first 5 rows on specs/dealers.csv as integration test opportunities

let me choose what car i want to search for, at least model, through a local web ui

when scraping, filter for the model when doing the initial GET for the inventory to simplify the listing/filtering e.g. for an `express.*` kind of dealer inventory, use a url like this: `https://express.bmwsf.com/inventory?f=submodel%3AiX` - add the  year, too, e.g. `https://express.bmwsf.com/inventory?f=submodel%3AiX&f=year%3A2026` and 

- hardcode year to 2026, no need to look for other years.
- hardcode model to the "iX"
- make sure the chromium urls have the URL parameters