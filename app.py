import streamlit as st
import json
import time
import requests

# ページ設定
st.set_page_config(
    page_title="Instagram Follower Bio Searcher",
    page_icon="🔍",
    layout="wide"
)

# Actor IDs
FOLLOWERS_ACTOR = "datadoping~instagram-followers-scraper"
PROFILE_ACTOR = "apify~instagram-profile-scraper"


def run_actor(api_token: str, actor_id: str, payload: dict, timeout: int = 600, status_placeholder=None) -> list:
    """Actorを実行して結果を返す"""
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    params = {"token": api_token}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, params=params, json=payload)

    if response.status_code != 201:
        st.error(f"Error: {response.status_code} - {response.text[:200]}")
        return []

    run_id = response.json()["data"]["id"]

    # 完了待機
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    start_time = time.time()

    while time.time() - start_time < timeout:
        resp = requests.get(status_url, params=params)
        if resp.status_code == 200:
            status = resp.json()["data"]["status"]
            if status_placeholder:
                status_placeholder.text(f"Status: {status}")

            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                st.error(f"Failed: {status}")
                return []
        time.sleep(3)
    else:
        st.error("Timeout")
        return []

    # 結果取得
    results_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"
    resp = requests.get(results_url, params=params)
    return resp.json() if resp.status_code == 200 else []


def init_session_state():
    """セッション状態を初期化"""
    if "processed_users" not in st.session_state:
        st.session_state.processed_users = set()
    if "all_followers" not in st.session_state:
        st.session_state.all_followers = []
    if "privacy_map" not in st.session_state:
        st.session_state.privacy_map = {}
    if "results" not in st.session_state:
        st.session_state.results = []
    if "current_target" not in st.session_state:
        st.session_state.current_target = ""


def main():
    st.title("🔍 Instagram Follower Bio Searcher")
    st.markdown("特定アカウントのフォロワーから、bioにキーワードを含むユーザーを検索")

    # セッション状態初期化
    init_session_state()

    # サイドバー: 設定
    with st.sidebar:
        st.header("⚙️ 設定")

        api_token = st.text_input(
            "Apify API Token",
            type="password",
            help="Apifyのダッシュボード → Settings → Integrations から取得"
        )

        st.markdown("---")

        target_username = st.text_input(
            "ターゲットアカウント",
            placeholder="naganuma_17th",
            help="フォロワーを検索するアカウント（@なし）"
        )

        search_term = st.text_input(
            "検索キーワード",
            value="05",
            help="bioに含まれるキーワード"
        )

        st.markdown("---")

        max_followers = st.slider(
            "最大フォロワー取得数",
            min_value=100,
            max_value=2000,
            value=1000,
            step=100,
            help="コスト管理用"
        )

        max_profiles = st.slider(
            "1回あたりのプロフィール取得数",
            min_value=50,
            max_value=500,
            value=100,
            step=50,
            help="1回の実行で取得するプロフィール数"
        )

        st.markdown("---")
        st.markdown("### 💰 コスト目安（1回あたり）")
        st.markdown(f"- フォロワー取得: ~${max_followers * 0.001:.2f}")
        st.markdown(f"- プロフィール取得: ~${max_profiles * 0.01:.2f}")

        st.markdown("---")
        st.markdown("### 📊 現在の状態")
        st.markdown(f"- 処理済み: **{len(st.session_state.processed_users)}** 人")
        st.markdown(f"- フォロワーリスト: **{len(st.session_state.all_followers)}** 人")
        st.markdown(f"- マッチ数: **{len(st.session_state.results)}** 件")

    # ターゲットが変わったらリセット（結果は保持）
    if target_username and target_username != st.session_state.current_target:
        if st.session_state.current_target != "":
            st.session_state.processed_users = set()
            st.session_state.all_followers = []
            st.session_state.privacy_map = {}
            # results は保持（累積）
        st.session_state.current_target = target_username

    # メイン: 実行ボタン
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        run_button = st.button("🚀 検索開始（続きから）", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 フォロワー再取得", use_container_width=True):
            st.session_state.all_followers = []
            st.session_state.privacy_map = {}
            st.rerun()

    with col3:
        if st.button("🗑️ 全てリセット", use_container_width=True):
            st.session_state.processed_users = set()
            st.session_state.all_followers = []
            st.session_state.privacy_map = {}
            st.session_state.results = []
            st.rerun()

    # 実行処理
    if run_button:
        if not api_token:
            st.error("❌ Apify API Tokenを入力してください")
            return
        if not target_username:
            st.error("❌ ターゲットアカウントを入力してください")
            return

        # Stage 1: フォロワーリスト取得（未取得の場合のみ）
        st.markdown("### 🔹 Stage 1: フォロワーリスト")

        if not st.session_state.all_followers:
            status1 = st.empty()
            progress1 = st.progress(0)

            followers_payload = {
                "usernames": [target_username],
                "max_count": max_followers,
            }

            status1.text("Starting follower collection...")
            progress1.progress(10)

            followers = run_actor(api_token, FOLLOWERS_ACTOR, followers_payload, timeout=300, status_placeholder=status1)
            progress1.progress(100)

            if not followers:
                st.error("❌ フォロワーが取得できませんでした")
                return

            # セッションに保存
            st.session_state.all_followers = followers
            st.session_state.privacy_map = {f.get("username"): f.get("is_private", True) for f in followers}

            st.success(f"✅ {len(followers)} フォロワーを取得（新規）")
        else:
            st.info(f"📋 キャッシュ済み: {len(st.session_state.all_followers)} フォロワー")

        # フォロワー情報表示
        followers = st.session_state.all_followers
        public_count = len([f for f in followers if not f.get("is_private", True)])
        private_count = len(followers) - public_count

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Followers", len(followers))
        col2.metric("Public", public_count)
        col3.metric("Private", private_count)

        # 未処理ユーザーを特定
        all_usernames = [f.get("username") for f in followers]
        new_usernames = [u for u in all_usernames if u not in st.session_state.processed_users]

        st.info(f"📊 未処理: {len(new_usernames)} / {len(all_usernames)} 人")

        if not new_usernames:
            st.success("✅ 全ユーザー処理済み！")
            return

        # Stage 2: 未処理ユーザーのプロフィール取得
        st.markdown("### 🔹 Stage 2: プロフィール詳細取得")
        status2 = st.empty()
        progress2 = st.progress(0)

        # 未処理から上限分を取得
        usernames_to_check = new_usernames[:max_profiles]

        profile_payload = {
            "usernames": usernames_to_check,
        }

        status2.text(f"Getting {len(usernames_to_check)} new profiles...")
        progress2.progress(10)

        profiles = run_actor(api_token, PROFILE_ACTOR, profile_payload, timeout=600, status_placeholder=status2)
        progress2.progress(100)

        if not profiles:
            st.error("❌ プロフィールが取得できませんでした")
            return

        st.success(f"✅ {len(profiles)} プロフィールを取得")

        # 処理済みに追加
        for p in profiles:
            st.session_state.processed_users.add(p.get("username", ""))

        # フィルタリング
        st.markdown(f"### 🔍 '{search_term}' でフィルタリング")

        new_matches = []
        existing_usernames = {r["username"] for r in st.session_state.results}

        for p in profiles:
            bio = p.get("biography", "") or ""
            username = p.get("username", "")
            is_private = st.session_state.privacy_map.get(username, True)

            if search_term in bio and username not in existing_usernames:
                new_matches.append({
                    "username": username,
                    "full_name": p.get("fullName", ""),
                    "bio": bio,
                    "url": f"https://www.instagram.com/{username}/",
                    "is_private": is_private,
                    "status": "非公開" if is_private else "公開",
                })

        # 結果に追加
        st.session_state.results.extend(new_matches)

        st.success(f"✨ 今回: {len(new_matches)} 件ヒット / 累計: {len(st.session_state.results)} 件")

        # 残り件数
        remaining = len(new_usernames) - len(usernames_to_check)
        if remaining > 0:
            st.warning(f"📊 残り {remaining} 人未処理。もう一度「検索開始」を押してください。")

    # 結果表示
    if st.session_state.results:
        st.markdown("---")
        st.markdown("## 📋 結果（累計）")

        results = st.session_state.results

        # サマリー
        public_matches = len([r for r in results if not r["is_private"]])
        private_matches = len(results) - public_matches

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Matches", len(results))
        col2.metric("Public", public_matches)
        col3.metric("Private", private_matches)

        # テーブル表示
        st.markdown("### 一覧")
        for i, r in enumerate(results, 1):
            status_emoji = "🔓" if not r["is_private"] else "🔒"
            with st.expander(f"{i}. {status_emoji} @{r['username']} - {r['full_name']}"):
                st.markdown(f"**Bio:** {r['bio']}")
                st.markdown(f"**URL:** [{r['url']}]({r['url']})")
                st.markdown(f"**Status:** {r['status']}")

        # ダウンロード
        st.markdown("### 📥 ダウンロード")

        col1, col2 = st.columns(2)

        with col1:
            json_str = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 JSONダウンロード",
                data=json_str,
                file_name="instagram_bio_search_results.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            # CSV形式
            csv_lines = ["username,full_name,bio,url,status"]
            for r in results:
                bio_escaped = r["bio"].replace('"', '""').replace('\n', ' ')
                csv_lines.append(f'"{r["username"]}","{r["full_name"]}","{bio_escaped}","{r["url"]}","{r["status"]}"')
            csv_str = "\n".join(csv_lines)

            st.download_button(
                label="📥 CSVダウンロード",
                data=csv_str,
                file_name="instagram_bio_search_results.csv",
                mime="text/csv",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
