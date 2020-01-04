from geopy.geocoders import Nominatim
import requests  # API利用時に便利
import re
import datetime

# NominatimはOpenStreetMapというサイトのサーチエンジンでもあり、
# サイト上から緯度・経度を確認することもできます。

# 場所名から緯度・経度を算出する自作の関数geocoding(place)を定義
# 普段から関数を作る習慣をつけておくと良いでしょう。


def geocoding(place):
    geolocator = Nominatim(user_agent="my-application")
    # 関数定義の下の1行目でNominatimに接続するためにuser_agent（サーバーに送信するユーザー情報、Nominatimの場合は
    # 以下の規約でアプリケーション名を指定することになっています）を設定
    location = geolocator.geocode(place, timeout=10)
    # 入力された場所の文字列(place)から位置情報を取得するコードを書きます。
    # geopyではデフォルトのタイムアウト時間が1秒となっており、サーバー混雑等の影響によりタイムアウトとなってしまう可能性を下げるため、
    # ここではtimeout=10(秒)としています。
    if location is None:
        return
    else:
        latitude = location.latitude  # 緯度
        longitude = location.longitude  # 経度
        return latitude, longitude  # 出力
        # 位置情報が取得できた場合とできなかった場合の処理を分けて記述します。
        # 場所から正しく位置情報を取得できない場合は、locationの中身がNoneとなるため、
        # その場合は、returnで緯度・経度もNoneとして出力します。
        # returnの後ろに何もつけなかった場合はNoneが出力されます。


# これで「場所」を入力すると「緯度・経度」が出力される関数geocoding(place)ができました。
# 楽天トラベル空室検索APIを利用して、ホテルの空室検索を行う関数hotel_search(place, checkin, checkout)を定義
# この関数に"場所名","チェックイン日","チェックアウト日"を通すことにより、LINE BOTの
# メッセージとして送信する文章を出力することを目的とします。


def hotel_search(place, checkin, checkout):  # 場所とチェックイン日とチェックアウト日を引数としています。
    latitude, longitude = geocoding(place)
    # APIに通すためには場所名を緯度・経度に変換する必要があるため、まずは先ほど作成した関数geocodingに場所名placeを入力して、緯度・経度をそれぞれ取得します。
    # from geopy.geocoders import Nominatim

    # URLとURLパラメータを設定
    # requestsライブラリによりAPIを利用する際に毎回必要となる一般的な手順になります。
    url = "https://app.rakuten.co.jp/services/api/Travel/VacantHotelSearch/20170426"
    params = {
        "applicationId": "1071198031638624552",
        "formatVersion": "2",
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "latitude": latitude,
        "longitude": longitude,
        "searchRadius": "3",  # 緯度、経度で指定した場所からの距離(検索半径、km)
        "datumType": "1",  # 緯度、経度のタイプ 1=世界測地系
        "maxCharge": "5000",
        "minCharge": "1500",
        "hits": "5",
    }  # 取得件数

    # APIへ接続し辞書形式でデータを得る
    # requests.getにより設定したURLとパラメータを元にGET通信を行います。
    # 次に、requestsライブラリの関数json()により変数contentにデコードしたjsonデータを辞書として格納します。
    # requestsなどにより外部と通信するプログラムの場合は、通信エラーが予期されるため、try～except文でエラー処理を行うと良い。
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
            + "の半径3km以内に合計"
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
        # import traceback
        # traceback.print_exc()
        return "API接続中に何らかのエラーが発生しました"
        # 空室が見つからなかったときや過去の日付を指定してしまったときなど、正常にAPIと通信ができていて、
        # かつAPIからエラー情報が返ってきた場合の処理を記述


# LINE上で送信した文章を楽天APIに通すためのデータに加工する
# 文章からキーワード（場所、チェックイン日、宿泊日数）を抽出するプログラムを最後に書きます。


def extract_words(str):
    place_search = re.search("「(.+?)」", str)
    time_search = re.search(r"\d{4}/\d{1,2}/\d{1,2}", str)
    period_search = re.search("\D(\d{1,2})泊", str)
    # 正規表現reライブラリのsearch関数により目的のキーワードが文章に含まれているかを判定します。
    # 以下の条件に合致した場合、それぞれの変数に代入します。
    # 場所は、"「場所」"　→　"place_search"
    # ・チェックイン日は、"0000/00/00" 　→　time_search"
    # ・宿泊日数は、"00泊"　→　"term_search"
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

    # 引数の先頭に*をつけることにより、タプルやリストを展開して関数に渡すことができます。
