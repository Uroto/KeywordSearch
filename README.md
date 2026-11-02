# 創作ライフ キーワード調査ツール

Windows のローカル環境で実行する Streamlit 製キーワード調査ツールです。Google Ads API の認証情報が未設定でも、ダミーデータを使って画面・一括処理・CSV・グラフの一連の動作を確認できます。

## セットアップ

1. Python 3.11 以降をインストールします（インストール時に Python Launcher `py` を有効化）。
2. このフォルダで `py -m pip install -r requirements.txt` を実行します。
3. `start.bat` をダブルクリックするか、`py -m streamlit run app.py` を実行します。
4. ブラウザで表示されたローカル URL を開きます。

## Google Ads API の有効化

1. `.env.example` を `.env` にコピーします。
2. Google Cloud Console で Google Ads API を有効化し、OAuth クライアントを作成します。API のアクセスレベルは、この OAuth クライアントを所有する Cloud プロジェクトに付与されます。
3. Google Cloud Console の Google Ads API Overview で、ブランド確認を完了して **Basic 以上**のアクセスレベルを申請します。検索指標・キーワード候補で使用する `KeywordPlanIdeaService` は Explorer アクセスでは利用できません。
4. 設定画面で OAuth クライアント情報、リフレッシュトークン、お客様 ID を入力します。
5. 保存後、キーワード調査画面は Google Ads API モードへ切り替わります。

Developer Token は 2026年9月9日に廃止されました。このツールは Developer Token を使用・送信せず、OAuth クライアントを所有する Google Cloud プロジェクトの API アクセスレベルを使用します。`KeywordPlanIdeaService` による候補・検索指標の取得には、有効な OAuth 認証情報と、Google Cloud Console で設定した API アクセスレベルが必要です。API エラー時は、OAuth クライアントの Cloud プロジェクト、アクセスレベル、OAuth の権限・お客様 ID を確認してください。

## 作成方法・免責事項

このツールは、AI を用いたバイブコーディングにより作成されています。作者は、本ツールに関する修正、機能追加、問い合わせ対応、技術サポートを一切行いません。

本ツールは現状有姿で提供されます。本ツールの利用、利用不能、出力結果、Google Ads API の利用、またはこれらに起因して生じた直接的・間接的な損害、不利益、データ損失、機会損失等について、作者は一切の責任を負いません。利用者の責任において内容を確認したうえで使用してください。

認証情報はローカルの `.env` にのみ保存され、`.gitignore` で Git 管理から除外されます。`.env` を共有・公開しないでください。

## データの扱い

- 検索指標は 30 日、関連キーワードは 7 日を JSON キャッシュします（設定画面で変更可）。
- キャッシュは `data/keyword_cache.json` に自動作成され、破損時は空のキャッシュとして安全に再開します。
- CSV は UTF-8（BOM付き）で出力するため、Excel で開きやすい形式です。インポートは UTF-8 と CP932 に対応します。
- Google Ads API の数値は広告プランニング用の指標です。ダミーモードの値は実測値・推定値のいずれでもありません。
