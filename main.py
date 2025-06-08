import yagmail
import yfinance as yf
from pytrends.request import TrendReq
from datetime import datetime

def send_email(subject, body, to_email, user, password):
    yag = yagmail.SMTP(user, password)
    yag.send(to=to_email, subject=subject, contents=body)

def main():
    now = datetime.now().strftime("%Y-%m-%d")
    keywords = ["AI", "반도체", "전기차"]
    codes = ["005930.KS", "000660.KS", "035420.KS"] # 삼성전자, SK하이닉스, NAVER

    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload(keywords, timeframe='today 1-m', geo='KR')
    trend_df = pytrends.interest_over_time()
    body = [f"[{now} 한국 주식 추천]"]

    for keyword, code in zip(keywords, codes):
        trend_series = trend_df[keyword]
        price_df = yf.download(code, period='1mo')
        price_series = price_df["Close"]

        # 날짜 인덱스 동기화 (공통 날짜만)
        common_dates = trend_series.index.intersection(price_series.index)
        trend_series = trend_series.loc[common_dates]
        price_series = price_series.loc[common_dates]

        # 변화율 계산
        trend_change = trend_series.pct_change().dropna()
        price_change = price_series.pct_change().dropna()

        # 변화율 시리즈의 인덱스도 동기화(상관계수 계산 전)
        common_index = trend_change.index.intersection(price_change.index)
        trend_change = trend_change.loc[common_index]
        price_change = price_change.loc[common_index]

        # 데이터가 2개 이상일 때만 상관계수 계산
        if len(trend_change) > 1 and len(price_change) > 1:
            corr = trend_change.corr(price_change)
            # 최근 7일 평균 > 그 전 평균 여부 체크 (데이터 7개 이상만 판단)
            if len(trend_series) > 7 and corr > 0.3 and trend_series[-7:].mean() > trend_series[:-7].mean():
                body.append(f"🔔 [{keyword}] 관련 {code} 추천 (상관계수: {corr:.2f})")
            else:
                body.append(f"ℹ️ [{keyword}] 관련 {code} 특별 추천 없음 (상관계수: {corr:.2f})")
        else:
            body.append(f"⚠️ [{keyword}] 관련 데이터 부족 (종목: {code})")

    # GitHub Actions에서는 환경 변수(Secrets)에서 이메일 계정/비밀번호 받음
    import os
    user = os.environ['EMAIL_USER']
    password = os.environ['EMAIL_PW']
    send_email("오늘의 한국 증시 추천", "\n".join(body), "dlalswo30339@gmail.com", user, password)

if __name__ == "__main__":
    main()
