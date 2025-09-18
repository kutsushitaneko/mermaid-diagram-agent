## smolagents サンプルコード集

このリポジトリは、Qiita 記事「コードエージェント smolagents でAIエージェントを始めよう！ - AI駆動開発ツール自作編」で紹介しているサンプルコード一式です。記事内の解説とあわせてお使いください。

- 記事: [コードエージェント smolagents でAIエージェントを始めよう！ - AI駆動開発ツール自作編](https://qiita.com/yuji-arakawa/items/edff6a87c37517d79ba4)

### できること（概要）
- smolagents の `CodeAgent` を使った最小コード例（OCI Generative AI、OpenAI、Google）
- ウェブアクセス/外部API呼び出しのコード生成＆実行例
- Gradio UI で要件から Mermaid 図を自動生成（シーケンス図/フロー/ER 図など）
- MCP を通じた SQLcl のツール連携（DB メタデータから ER 図生成 等）


## 前提条件
- Python 3.10 以上（3.12 で動作検証）
- git
- node.js 18 以上（Mermaid 図生成用）
- npm で Mermaid CLI をグローバルインストール
  - `npm install -g @mermaid-js/mermaid-cli`
- （オプション・MCP 連携時）Oracle SQLcl 23.4+ をインストールし、実行パスを確認
  - 例: `D:\tools\sqlcl\bin\sql.exe`


## クローンとセットアップ

1) リポジトリの取得
- GitHub からクローン
```bash
git clone https://github.com/kutsushitaneko/mermaid-diagram-agent.git
cd mermaid-diagram-agent
```
- もしくは ZIP をダウンロードして展開

2) Python 仮想環境の作成と有効化（例: Windows / PowerShell）
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate
```
macOS/Linux の例:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) 依存パッケージのインストール
```bash
pip install -U pip
pip install -r requirements.txt
```

4) smolagentsライブラリ最新版をGitHubからインストール（[issue #1765](https://github.com/huggingface/smolagents/issues/1765) 対策の[PR #1766](https://github.com/huggingface/smolagents/pull/1766) がマージされている最新版（1.22.0.dev0 以上）をインストール）
```bash:GitHub から直接インストール
pip install -U "smolagents[litellm,toolkit,gradio,mcp]@git+https://github.com/huggingface/smolagents.git"
```
```bash:インストールされたバージョンの確認例
$ pip show smolagents
Name: smolagents
Version: 1.22.0.dev0
Location: H:\lab\smolagents\mermaid-diagram-agent\.venv\Lib\site-packages
Requires: huggingface-hub, jinja2, pillow, python-dotenv, requests, rich
Required-by:
```
Versions が 1.22.0.dev0 以上となっていれば OK です。

5) Mermaid CLI（mmdc）のインストール
```bash
npm install -g @mermaid-js/mermaid-cli
```

6) Oracle SQLcl のインストール
[コード開発AIエージェント Cline ＋ LiteLLM + OCI Generative AI Grok 4 + Oracle Database MCP サーバーでAI駆動開発を始める](https://qiita.com/yuji-arakawa/items/458eebda52b7fb4a4dc1#sqlcl-%E3%81%AE%E8%A8%AD%E5%AE%9A%E6%89%8B%E9%A0%86) を参照してインストール

7) 環境変数の設定（.env 推奨）
プロジェクト直下に `.env` を作成し、必要なキーを設定します。
```dotenv
# === OCI Generative AI (xAI Grok-4) 用 ===
OCI_USER=ocid1.user.oc1..example
OCI_FINGERPRINT=aa:bb:cc:dd:ee:ff:...
OCI_TENANCY=ocid1.tenancy.oc1..example
OCI_REGION=us-chicago-1
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..example
# PEM の内容を 1 つの環境変数に格納します（改行は \n で表現）
OCI_KEY="-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----\n"

# === OpenAI 用（任意）===
OPENAI_API_KEY=sk-...

# === Google Generative AI 用（任意）===
GOOGLE_API_KEY=AIza...
```


## 各コード例の起動方法

事前に仮想環境を有効化し、`.env` を用意してから実行してください。以下はすべてプロジェクト直下での実行例です。

### 1) 最小コードエージェント（OCI Generative AI）
```bash
python 100_simple_codeagent.py
```
必要: `OCI_*` 環境変数（xAI Grok-4 を利用）。

### 2) 最小コードエージェント（OpenAI）
```bash
python OpenAI_100_simple_codeagent.py
```
必要: `OPENAI_API_KEY`。

### 3) 最小コードエージェント（Google Generative AI）
```bash
python Google_100_simple_codeagent.py
```
必要: `GOOGLE_API_KEY`。

### 4) ウェブアクセス（スクレイピング）コード生成/実行例
```bash
python 200_web_access_codeagent.py
```

### 5) 外部 Web API 呼び出しコード生成/実行例
```bash
python 300_web_api_codeagent.py
```

### 6) システム設計支援エージェント（Gradio UI）
```bash
python 400_system_design_agent_gradio.py
```
必要: `OCI_*` と `@mermaid-js/mermaid-cli`（`mmdc`）。
- 実行後、ターミナルに表示されるローカル URL（例: http://127.0.0.1:7860/ ）をブラウザで開きます。
- 生成した Mermaid 図の `.png` と `.mmd` は `output/` に保存されます。

### 7) システム設計支援エージェント（MCP + SQLcl 連携付き）
```bash
python 500_system_design_agent_gradio_with_MCP.py
```
- コード内の SQLcl パスを環境に合わせて修正してください。
  - 既定: `D:\\tools\\sqlcl\\bin\\sql.exe`
- SQLcl の `-mcp` を用いて MCP サーバとして起動し、エージェントから DB 情報取得ツール群にアクセスします。


## よくあるエラーと対処
- `mmdc command not found`: `npm install -g @mermaid-js/mermaid-cli` を実行し、シェルを再起動。
- OCI 周りの認証エラー: `.env` の `OCI_*` 値（特に `OCI_KEY` の PEM 文字列）を再確認。リージョン/コンパートメントも正しいか確認。
- Gradio の履歴が長くなりエラー: 本サンプルは履歴リセット機能を実装していません。必要に応じてアプリを再起動してください（記事も参照）。


## 参考リンク
- Qiita 記事: [コードエージェント smolagents でAIエージェントを始めよう！ - AI駆動開発ツール自作編](https://qiita.com/yuji-arakawa/items/edff6a87c37517d79ba4)


## ライセンス
本リポジトリは MIT No Attribution（MIT-0）で提供します。


