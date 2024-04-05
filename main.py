import io
import time
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


URL = "https://bordeauxindex.com/livetrade/next-page"


def get_cookie():
    res = requests.get("https://bordeauxindex.com/livetrade/marketplace")
    cookie = "; ".join([f"{x.name}={x.value}" for x in res.cookies])
    xsrf_token = [x.value for x in res.cookies if x.name == "XSRF-TOKEN"][0]
    return unquote(xsrf_token), unquote(cookie)


def main():
    page = 1
    xsrf_token, cookie = get_cookie()
    headers = {
        "x-xsrf-token": xsrf_token,
        "content-type": "application/json",
        "cookie": cookie
    }
    writer = io.StringIO()
    writer.write(
        "vintage,wine_name,wine_detail,case_description,last_trade_per_case,"
        "sell_quantity,bid_per_case,spread,offer_per_case,buy_quantity\n"
    )
    try:
        while True:
            print(f"Page: {page}")
            request_body = {
                "page": page,
                "category": "",
                "vintage": "",
                "region": "",
                "packsize": "",
                "colour": "",
                "price": "",
                "search": ""
            }
            res = requests.post(URL, headers=headers, json=request_body)
            response = res.json()

            market_rows = response.get("marketRows")

            soup = BeautifulSoup(market_rows, "html.parser")
            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                vintage = tds[1].get_text().strip()
                wine_name, wine_detail = get_wine_name_and_details(tds[2])
                case_description = tds[4].get_text().strip()
                last_trade_per_case = get_last_trade_per_case(tds[5])
                sell_quantity = tds[8].get_text().strip()
                bid_per_case = tds[9].get_text().strip()
                spread = tds[10].get_text().strip()
                offer_per_case = tds[11].get_text().strip()
                buy_quantity = tds[12].get_text().strip()
                writer.write(
                    f'"{vintage}","{wine_name}","{wine_detail}","{case_description}",'
                    f'"{last_trade_per_case}","{sell_quantity}","{bid_per_case}","{spread}",'
                    f'"{offer_per_case}","{buy_quantity}"\n'
                )
            if response.get("nextPage") is None or page == 3:
                break
            page = response.get("nextPage")
            time.sleep(1)
    except Exception as exc:
        print(f"Error: {exc}")
        raise

    with open("./output.csv", "w") as f:
        f.write(writer.getvalue())

    writer.close()


def get_wine_name_and_details(td):
    spans = td.find_all("span")
    wine_name = spans[0].get_text().strip()
    wine_detail = spans[1].contents[2].strip()
    return wine_name, wine_detail


def get_last_trade_per_case(td):
    try:
        trade = td.contents[0].strip()
        last_date = td.contents[3].get_text().strip()
        return f"{trade} ({last_date})"
    except:
        return ""


if __name__ == '__main__':
    main()
