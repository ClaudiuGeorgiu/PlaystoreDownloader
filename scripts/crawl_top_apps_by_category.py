#!/usr/bin/env python3

import os
from urllib.parse import urlparse, parse_qs

from playstore.playstore import Playstore


def main():
    # Use the private credentials for this script.
    api = Playstore(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            os.path.pardir,
            "private_credentials.json",
        )
    )

    # Get the categories in the Google Play Store.
    res = api.protobuf_to_dict(api.get_store_categories())["category"]
    store_categories = set(
        map(lambda x: parse_qs(urlparse(x["dataUrl"]).query)["cat"][0], res)
    )

    # Get the top top_num free apps in each category.
    top_num = 100
    for cat in store_categories:
        doc = api.list_app_by_category(cat, "apps_topselling_free", top_num).doc[0]
        for app in doc.child if doc.docid else doc.child[0].child:
            downloads = app.details.appDetails.numDownloads
            rating = app.aggregateRating.starRating

            # Print package name, category, number of downloads and rating.
            print(f"{app.docid}|{cat}|{downloads}|{rating}")


if __name__ == "__main__":
    # Run the script from the main directory of the project by using this command:
    # pipenv run python -m scripts.crawl_top_apps_by_category
    main()
