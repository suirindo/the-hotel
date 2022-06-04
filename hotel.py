from geopy.geocoders import Nominatim
import requests  # API利用時に便利
import re
import datetime


def geocoding(place):
    geolocator = Nominatim(user_agent="my-application")

    location = geolocator.geocode(place, timeout=10)

    if location is None:
        return
    else:
        latitude = location.latitude  # 緯度
        longitude = location.longitude  # 経度
        return latitude, longitude  # 出力

def hotel_search(place, checkin, checkout):  
    latitude, longitude = geocoding(place)

    url = "https://app.rakuten.co.jp/services/api/Travel/VacantHotelSearch/20170426"
    params = {
        "applicationId": "1071198031638624552",
        "formatVersion": "2",
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "latitude": latitude,
        "longitude": longitude,
        "searchRadius": "1.0",  # 緯度、経度で指定した場所からの距離(検索半径、km)
        "datumType": "1",  # 緯度、経度のタイプ 1=世界測地系
        "maxCharge": "5000",
        "minCharge": "1500",
        "hits": "10",  # 取得件数
    }

    try:
        r = requests.get(url, params=params)
        content = r.json()
        error = content.get("error")
        if error is not None:
            msg = content["error_description"]
            return msg
        hotel_count = content["pagingInfo"]["recordCount"]
        hotel_count_display = content["pagingInfo"]["last"]
        msg = (
            place
            + "の半径1.0km以内に、予算
            + str(minCharge)
            + "円〜"
            + str(maxCharge)
            + "円のホテルが合計"            
            + str(hotel_count)
            + "件見つかりました。"
            + str(hotel_count_display)
            + "件を表示します。\n"
        )
        for hotel in content["hotels"]:
            hotelname = hotel[0]["hotelBasicInfo"]["hotelName"]
            hotelurl = hotel[0]["hotelBasicInfo"]["hotelInformationUrl"]
            msg += "ホテル名:" + hotelname + ", URL:" + hotelurl + "\n"
        msg = msg.rstrip()
        return msg
    except Exception:

        return "API接続中に何らかのエラーが発生しました"


def extract_words(str):
    place_search = re.search("「(.+?)」", str)
    time_search = re.search(r"\d{4}/\d{1,2}/\d{1,2}", str)
    period_search = re.search("\D(\d{1,2})泊", str)

    error_msg = []
    # エラー文を格納する変数"error_msg"というリストを定義
    if place_search is None:
        error_msg.append("・場所が入力されていません。鍵括弧「」内に場所を入力してください。")
    if time_search is None:
        error_msg.append("・チェックイン日が入力されていません。XXXX/XX/XXの形式で入力してください。")
    if period_search is None:
        error_msg.append("・宿泊日数が入力されていません。○○泊の形式で泊をつけて、半角数字(最大二桁)で入力してください。")
    if error_msg:
        error_msg = "\n".join(error_msg)
        return error_msg
    # キーワードを変数に代入
    place = place_search.group(1)
    time = time_search.group()
    period = period_search.group(1)

    # 日付の書式をAPI用に変換
    period = int(period)
    # datetimeライブラリのdatetime.strptime関数により、チェックイン日として代入した変数"time"を日付オブジェクトとして認識、変数"checkin"に代入
    checkin = datetime.datetime.strptime(time, "%Y/%m/%d")
    # timedelta関数により宿泊期間をチェックイン日に加算し、それをチェックアウト日として変数"checkout"に代入
    checkout = checkin + datetime.timedelta(days=period)
    # 日付オブジェクトをXXXX-XX-XXという形式の文字列に変換
    checkin = checkin.strftime("%Y-%m-%d")
    checkout = checkout.strftime("%Y-%m-%d")
    return place, checkin, checkout
