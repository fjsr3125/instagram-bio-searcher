# Instagram Follower Bio Searcher

特定のInstagramアカウントのフォロワーから、bioに指定キーワードを含むユーザーを検索するツール。

## 機能要件

### 概要
- 対象アカウントのフォロワーリストを取得
- 各フォロワーのプロフィール詳細（bio）を取得
- 指定キーワードでbioをフィルタリング
- 公開/非公開アカウントの両方に対応

### 2段階アプローチ
| Stage | 処理内容 | 使用Actor |
|-------|---------|-----------|
| Stage 1 | フォロワーリスト取得 | datadoping/instagram-followers-scraper |
| Stage 2 | プロフィール詳細取得 | apify/instagram-profile-scraper |

### 主要機能
1. **フォロワー取得**: 対象アカウントの全フォロワーを取得（ログイン不要）
2. **プロフィール取得**: 各フォロワーのbio、名前、公開状態を取得
3. **キーワード検索**: bioに指定文字列を含むアカウントを抽出
4. **結果ダウンロード**: JSON/CSV形式でエクスポート

### 出力形式
```json
{
  "username": "example_user",
  "full_name": "名前",
  "bio": "プロフィール文",
  "url": "https://www.instagram.com/example_user/",
  "is_private": true,
  "status": "非公開"
}
```

---

## Web版（Streamlit）

### ローカル実行
```bash
# セットアップ
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開く。

### Streamlit Cloudへデプロイ（無料）

#### 1. GitHubにリポジトリ作成
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/instagram-bio-searcher.git
git push -u origin main
```

#### 2. Streamlit Cloudでデプロイ
1. [Streamlit Cloud](https://share.streamlit.io/) にアクセス
2. GitHubアカウントでログイン
3. 「New app」をクリック
4. リポジトリ、ブランチ（main）、ファイル（app.py）を選択
5. 「Deploy」をクリック

数分でデプロイ完了。URLが発行される。

### 使い方（Web版）
1. サイドバーで **Apify API Token** を入力（各自で取得）
2. **ターゲットアカウント** を入力
3. **検索キーワード** を設定
4. 「検索開始」ボタンをクリック
5. 結果をJSON/CSVでダウンロード

---

## CLI版（従来）

### セットアップ
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export APIFY_API_TOKEN='your_token_here'
```

### 実行
```bash
python find_05_followers.py
```

### 設定変更
`find_05_followers.py` の設定セクションを編集：

```python
TARGET_USERNAME = "naganuma_17th"  # 対象アカウント
SEARCH_TERM = "05"                  # 検索キーワード
MAX_FOLLOWERS = 800                 # 取得するフォロワー数上限
MAX_PROFILES_PER_RUN = 100          # 1回あたりのプロフィール取得数
```

### 複数回実行（コスト管理）
スクリプトは処理済みユーザーを記録するため、複数回実行しても重複取得しない：

```bash
# 1回目: 最初の100人をチェック
python find_05_followers.py

# 2回目: 次の100人をチェック（自動で未処理分から取得）
python find_05_followers.py
```

### リセット
```bash
rm processed_users.json results.json
```

---

## Apify APIトークンの取得方法

1. [Apify](https://apify.com/) でアカウント作成（無料）
2. ダッシュボード → Settings → Integrations
3. API Token をコピー

**無料枠**: $5/月（約500プロフィール分）

---

## コスト目安

| 処理 | 料金目安 |
|------|---------|
| フォロワー取得 | ~$0.001/件 |
| プロフィール取得 | ~$0.008-0.01/件 |

| フォロワー数 | 推定コスト |
|-------------|-----------|
| 100人 | ~$1 |
| 500人 | ~$5 |
| 1,000人 | ~$10 |

---

## 注意事項

- 非公開アカウントでもbioは取得可能（投稿のみ非公開）
- **非公開アカウントのフォロワーリストは取得不可**（Instagramの仕様）
- APIレート制限により、一度に取得できる数に制限がある場合あり
- クレジット不足時はActorがABORTEDになる
- Instagramの利用規約を確認してください
- Apifyの利用規約も確認してください

---

## ファイル構成

```
instagram_scraper/
├── app.py                 # Streamlit Webアプリ
├── find_05_followers.py   # CLI版スクリプト
├── requirements.txt       # 依存パッケージ
├── results.json          # 検索結果（自動生成）
├── processed_users.json  # 処理済みユーザー（自動生成）
└── README.md
```
