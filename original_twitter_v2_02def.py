# 必要なinstall
# pip install pandas
# pip install tweepy==4.5.0

# 必要なモジュールのimport
import pandas as pd
import tweepy
import config  # config.pyから情報を読み込む
from pytz import timezone

"""
メインの実行部分
ツイートデータの取得からデータの出力まで
"""
keyword = "デイトラ"
start_time = "2022-11-25T00:00:00Z"
end_time = "2022-11-28T00:00:00Z"
max_results = 50
rlcount = 3
print(type(rlcount))

# APIキー
consumer_key = config.CONSUMER_KEY
consumer_secret = config.CONSUMER_SECRET
access_token = config.ACCESS_KEY
access_token_secret = config.ACCESS_SECRET
baerer_token = config.BEARER_TOKEN

# tweepy.Clientでキーをセット
client = tweepy.Client(
    baerer_token, consumer_key, consumer_secret, access_token, access_token_secret
)


def main():
    # ツイートデータの取得##Twintなら、500件まで取得可能
    tweet_data = get_search_tweet(
        client, keyword, start_time, end_time, max_results, rlcount
    )
    # ツイートデータを番号順に出力
    out_put_tweets(tweet_data)
    # ツイートデータをDataFrameにする
    df = make_df(tweet_data)
    negapogi(df)
    # DataFrameの出力
    print(f"データフレーム{df}")
    # ツイートデータのCSVへの出力
    df.to_csv("tweets_data.csv", encoding='utf-8-sig')#文字化け対策


def get_search_tweet(client, keyword, start_time, end_time, max_results, rlcount):
    """
    ツイート情報を期間指定で収集
    取得できるデータは直近1週間以内
    RT+いいね数がrlcntを超えるツイートのみ取得
    """
    response = client.search_recent_tweets(
        query=keyword,
        start_time=start_time,  # YYYY-MM-DDTHH:mm:ssZ #直近7日以内
        end_time=end_time,
        expansions=["author_id"],
        tweet_fields=[
            "created_at",
            "public_metrics",
        ],  # reference "tweet.fields"→"tweet_fields" #ツイート日時、いいね・リツイート数等
        media_fields=["preview_image_url"],  # reference "media/fields"→"media_fields"
        max_results=max_results,  #
    )
    # print(response)
    # response.dataでツイート情報、response.includesで追加の情報を取得
    tweets = response.data
    includes = response.includes
    users = includes["users"]
    # ツイートのデータを取り出して、リストにまとめていく部分

    # ツイートデータを入れる空のリストを用意

    tweet_data = []
    for user, tweet in zip(users, tweets):  # 2つの関数
        # いいねとリツイートの合計がrefav_cnt以上の条件

        if (
            tweet.public_metrics["like_count"] + tweet.public_metrics["retweet_count"]
            > rlcount
        ):  # reference "public_metrics.like_count"→"puplic_metrics["like_count"]"

            # 空のリストtweet_dataにユーザーネーム、スクリーンネーム、RT数、いいね数、日付などを入れる
            tweet_data.append(
                [
                    user["name"],
                    user["username"],
                    tweet.public_metrics["retweet_count"],
                    tweet.public_metrics["like_count"],
                    tweet.public_metrics["quote_count"],
                    tweet.text.replace("\n", ""),  # replace: 改行コードの削除
                    tweet.created_at.astimezone(timezone("Asia/Tokyo")).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                ]  # creat_at :日時 ,timezone:UTC→TOKYOへ、.strfttime表示を修正
            )
    return tweet_data


def out_put_tweets(tweet_data):
    """
    ツイートのリストを順番に付けて出力する関数の作成
    """
    for i in range(len(tweet_data)):
        print(f"No.{i}{tweet_data[i]}")


def make_df(tweet_data):
    """
    ツイートのデータからDataFrameを作成する
    """
    # データを入れる空のリストを用意
    list_user_name = []
    list_user_id = []
    list_re_cnt = []
    list_fav_cnt = []
    list_quote_cnt = []
    list_data = []
    list_text = []
    # ツイートデータからユーザー名、ユーザーid、RT数、いいね数、日付け、ツイート本文のそれぞれをデータごとにまとめたリストを作る
    for i in range(len(tweet_data)):
        list_user_name.append(tweet_data[i][0])
        list_user_id.append(tweet_data[i][1])
        list_re_cnt.append(tweet_data[i][2])
        list_fav_cnt.append(tweet_data[i][3])
        list_quote_cnt.append(tweet_data[i][4])
        list_text.append(tweet_data[i][5])
        list_data.append(tweet_data[i][6])
    # 先ほど作ったデータごとにまとめたリストからDataframeの作成
    df = pd.DataFrame(
        {
            "ユーザー名": list_user_name,
            "ユーザーid": list_user_id,
            "RT数": list_re_cnt,
            "いいね数": list_fav_cnt,
            "引用数": list_quote_cnt,
            "日時": list_data,
            "本文": list_text,
        }
    )
    return df

# 形態素解析をするためのjanomeをimport
from janome.tokenizer import Tokenizer
# pandas

'''
データフレームを引数に受け取り、
ネガポジ分析をする関数
'''
def negapogi(df):
    # 極性辞書をPythonの辞書にしていく
    np_dic ={}
    with open ("pn.csv.m3.120408.trim", "r", encoding = "utf-8") as f: # 日本語評価極性辞書のファイルの読み込み # "r":読み込みモード
        lines = [line.replace("\n", "").split("\t") for line in f.readlines()]# 1行1行を読み込み、文字列からリスト化。リストの内包表記の形に
        #.split("\t") :タブで区切ってリスト化

    # リストからデータフレームの作成
    posi_nega_df = pd.DataFrame(lines, columns = ["word", "score", "explain"])
    # データフレームの2つの列から辞書の作成　zip関数を使う
    np_dic = dict(zip(posi_nega_df["word"], posi_nega_df["score"]))
    #print(np_dic)

    # 形態素解析をするために必要な記述を書いていく
    tokenizer = Tokenizer()
    # ツイート一つ一つを入れてあるデータフレームの列（本文の列）をsentensesと置く
    sentences = df["本文"]
    #sentences = ["憧れの先輩に悪く言われた", "彼女が結婚したのは控えめに言って嬉しい"]
    # p,n,e,?p?nを数えるための辞書を作成
    result = {"p": 0, "n": 0, "e": 0, "?p?n": 0}

    for sentence in sentences: # ツイートを一つ一つ取り出す
        for token in tokenizer.tokenize(sentence): # 形態素解析をする部分
            word = token.surface # ツイートに含まれる単語を抜き出す #形態素解析された文字を取り出す
            if word in np_dic: # 辞書のキーとして単語があるかどうかの存在確認
                value = np_dic[word] # 値(pかnかeか?p?nのどれか)をvalueという文字で置く
                if value in result: # キーの存在確認
                    result[value] += 1 # p,n,e,?p?nの個数を数える
    #総和を求める
    summary = result["p"]+result["n"]+result["e"]+result["?p?n"]
    # ネガポジ度の平均（pの総数 / summary, nの総数 / summary）を数値でそれぞれ出力
    # summaryが0の場合もあるので、try-exceptで例外処理
    try:
        #result["p"] / summary# ポジティブ度の平均
        #result["n"] / summary# ネガティブ度の平均
        print("ポジティブ度:",result["p"] / summary) # ポジティブ度の平均
        print("ネガティブ度:",result["n"] / summary) # ネガティブ度の平均
    except ZeroDivisionError:
        print("0です。")
    # summaryが0の場合

# print(df)
# 実行部分
if __name__ == "__main__":
    main()
