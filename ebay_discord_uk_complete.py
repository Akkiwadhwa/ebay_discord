import datetime
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

dict1 = {"condition_new": "false",
         "condition_used": "true",
         "delivery": "true",
         "collection": "true"}
pickup = ""

if dict1["condition_new"] == "true" and dict1["condition_used"] == "true":
    cond = "1000%7C3000"
elif dict1["condition_new"] == "true" and dict1["condition_used"] == "false":
    cond = "1000"
elif dict1["condition_new"] == "false" and dict1["condition_used"] == "true":
    cond = "3000"
elif dict1["condition_new"] == "false" and dict1["condition_used"] == "false":
    cond = None
else:
    cond = "1000"

if dict1["delivery"] == "true" and dict1["collection"] == "true":
    pickup = 1
else:
    pickup = 0

s_term = input("Please input search term: ").replace(" ", "+")
radius = input("Enter radius in miles(10,25,50,100,200,500,1000): ")
options = Options()
ua = UserAgent()
userAgent = ua.random
options.add_argument("--headless")
options.add_argument(f'user-agent={userAgent}')
link1 = input("webhook link: ")
url = f"https://www.ebay.co.uk/sch/i.html?_nkw={s_term}&LH_ItemCondition={cond}&_fcid=3&_dmd=1&_fsrp=1&_sop=10" \
      f"&rt=nc&_stpos=N10JB&_sadis={radius}&LH_LPickup={pickup}"

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

driver.get(url)
print(url)
new = []


def ebay():
    while True:
        li1 = []
        driver.refresh()
        time.sleep(2)
        data = driver.page_source
        soup = BeautifulSoup(data, "lxml")
        li = soup.select_one("#srp-river-results").select(".s-item.s-item__pl-on-bottom")
        for i in li[:10]:
            try:
                id = i.find("a")["href"].split("?")[0].split("/")[-1]
                title = i.select_one(".s-item__info.clearfix").select_one(".s-item__title").text
                price = i.find("span", class_="s-item__price").text
                link = i.find("div", class_="s-item__info").find("a")["href"]
            except:
                print(
                    "Some keywords show error while scraping,try this keyword after some time or try another key word.")
                print("Program exit")
                break
            else:
                payload = {"title": title.replace("New listing", ""),
                           "price": price,
                           "link": link,
                           "id": id}
                li1.append(payload)

        df_new = pd.DataFrame(li1)
        try:
            df_old = pd.read_csv(f'{s_term}.csv')
        except:
            df = pd.DataFrame([{"title": "",
                                "price": "",
                                "link": "",
                                "id": ""}])
            df.to_csv(f"{s_term}.csv")
            print("csv not found")
            print(f"{s_term}.csv created, Restarting the program. ")
            ebay()
        else:
            df12 = pd.concat([df_new, df_old])
            time.sleep(1)
            df12.drop_duplicates(subset=["title"], keep=False, inplace=True)
            time.sleep(1)
            df_new.to_csv(f'{s_term}.csv', index=False)
            added = df12.to_dict("records")
            if len(added) < 5:
                print(f"Sent to Discord server: {len(added)}  {datetime.datetime.utcnow()}")
                for i in added:
                    print("checking for duplicates.")
                    if i["title"] not in new:
                        print(i)
                        webhook = DiscordWebhook(
                            url=link1
                        )
                        embed = DiscordEmbed(title=f'{i["title"]}\n{i["price"]}', description=f"'{i['link']}'",
                                             color='03b2f8')
                        webhook.add_embed(embed)
                        time.sleep(1.5)
                        response = webhook.execute()
                        new.append(i["title"])


ebay()
