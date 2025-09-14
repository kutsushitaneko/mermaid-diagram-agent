import datetime
import os
import json
import re
from PIL import Image
import subprocess
import shutil
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, tool
import gradio as gr

load_dotenv()

oci_user = os.getenv("OCI_USER")
oci_fingerprint = os.getenv("OCI_FINGERPRINT")
oci_tenancy = os.getenv("OCI_TENANCY")
oci_region = os.getenv("OCI_REGION")
oci_key = os.getenv("OCI_KEY")
oci_compartment_id = os.getenv("OCI_COMPARTMENT_ID")

model = LiteLLMModel(
    model_id="oci/xai.grok-4",
    oci_region=os.getenv("OCI_REGION"),                    # 例: "us-ashburn-1"
    oci_user=os.getenv("OCI_USER"),                        # OCI User OCID
    oci_fingerprint=os.getenv("OCI_FINGERPRINT"),          # RSA key fingerprint
    oci_tenancy=os.getenv("OCI_TENANCY"),                  # Tenancy OCID
    oci_key=os.getenv("OCI_KEY"),                          # Private key content
    oci_compartment_id=os.getenv("OCI_COMPARTMENT_ID"),    # Compartment OCID
    temperature=0.0,
    max_tokens= 10000,
    drop_params=True
)

@tool
def get_mermaid_script_guidelines_tool() -> str:
    """
    Mermaid スクリプトの記法に関する注意事項を返すツール。

    Args:
        None
    
    Returns:
        Mermaid スクリプトの記法に関する注意事項
    """

    
    return """
    # Mermaid スクリプトを生成する際には、以下の注意事項を必ず守ってください。
    # Mermaid スクリプト全般の注意事項
        - ノードラベルに"<br>"は使えません。"<br>"の代わりに改行文字を使ってください。
        - ノードラベルに半角の"("と")"は使えません。半角の"("と")"の代わりに全角の"（"と"）"を使ってください。
        - subgraph の名前に空白が含まれる場合は二重引用符で囲んでください。
        - subgraph は直接エッジでつなげることはできません。ノード間をエッジでつなげてください。
    # ER図のMermaidスクリプトの注意事項
        - テーブル構造を表す場合の属性の構成要素は、データ型 カラム名 制約(PK, "NOT NULL", UK, CK, FK のいずれか) の順で記順してください。制約がない場合は、制約欄には何も書かないでください。
        - NUMBER にスケールは指定できません。NUMBER(精度,スケール)という記述はNGです。NUMBER(精度) とするかNUMBER とだけ記述してください。
        - VECTOR にデータフォーマットは指定できません。VECTOR(次元数, データフォーマット)という記述はNGです。VECTOR(次元数) とするか VECTOR とだけ記述してください。
    """

@tool
def generate_mermaid_diagram_tool(mermaid_script: str) -> str:
    """
    マーメイドダイアグラムの画像ファイルを生成するツール。
    生成したダイアグラムを png ファイルに保存し、ステータス、Mermaidスクリプトファイル名（mermaid_script_file）と 生成した画像ファイル名（diagram_file）などを JSON 形式で返す。

    Args:
        mermaid_script: ダイアグラムを生成するためのマーメイドスクリプト
    
    Returns:
        JSON string with the following schema:
        {
            "status": "success" | "fail", # 成功・失敗のステータス
            "mermaid_script_file": str | None, # マーメイドスクリプトのファイル名（パス名）
            "diagram_file": str | None, # 生成した画像ファイル名（パス名）
            "file_exists": bool, # 生成した画像ファイルが存在するかどうか
            "file_size": int | None, # 生成した画像ファイルのサイズ
            "error": str | None, # エラー内容
            "stdout": str, # 標準出力
            "stderr": str, # 標準エラー出力
            "command_output": str # コマンド実行結果
        }
    
    Example usage:
        mermaid_script = '''
        graph TD
            A[Start] --> B[Process]
            B --> C[End]
        '''
        result = generate_mermaid_diagram_tool(mermaid_script)      
    """
    
    # パラメータの検証
    if not mermaid_script or not mermaid_script.strip():
        return json.dumps({
            "status": "fail",
            "mermaid_script_file": None,
            "diagram_file": None,
            "file_exists": False,
            "file_size": None,
            "error": "mermaid_script is required and cannot be empty",
            "stdout": "",
            "stderr": "",
            "command_output": "Validation error: mermaid_script is required and cannot be empty"
        }, ensure_ascii=False)
    
    # outputディレクトリの存在確認と作成
    output_dir = "output"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        return json.dumps({
            "status": "fail",
            "mermaid_script_file": None,
            "diagram_file": None,
            "file_exists": False,
            "file_size": None,
            "error": f"Failed to create output directory: {str(e)}",
            "stdout": "",
            "stderr": "",
            "command_output": f"Directory creation error: {str(e)}"
        }, ensure_ascii=False)
    
    # ファイル名を生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mmd_file = f"{output_dir}/mermaid_diagram_{timestamp}.mmd"
    png_file = f"{output_dir}/mermaid_diagram_{timestamp}.png"
    
    # mermaidスクリプトをファイルに書き込み
    try:
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_script)
    except Exception as e:
        return json.dumps({
            "status": "fail",
            "mermaid_script_file": None,
            "diagram_file": None,
            "file_exists": False,
            "file_size": None,
            "error": f"Failed to write mermaid script file: {str(e)}",
            "stdout": "",
            "stderr": "",
            "command_output": f"File write error: {str(e)}"
        }, ensure_ascii=False)
    
    try:      
        # mmdcコマンドのフルパスを取得
        mmdc_path = shutil.which("mmdc")
        if mmdc_path is None:
            error_message = "mmdc command not found in PATH. Please install @mermaid-js/mermaid-cli using: npm install -g @mermaid-js/mermaid-cli"
            return json.dumps({
                "status": "fail",
                "mermaid_script_file": mmd_file if os.path.exists(mmd_file) else None,
                "diagram_file": None,
                "file_exists": False,
                "file_size": None,
                "error": error_message,
                "stdout": "",
                "stderr": "",
                "command_output": f"Path resolution error: {error_message}\nSearched in PATH: {os.environ.get('PATH', 'Not found')}"
            }, ensure_ascii=False)
        
        # mermaid CLIを使用してPNG生成（セキュリティ改善）
        result = subprocess.run(
            [mmdc_path, '-i', mmd_file, '-o', png_file, '--width', '2048', '--height', '2048'],
            capture_output=True,
            text=True,
            shell=False,  # セキュリティ向上
            encoding='utf-8',
            timeout=60  # タイムアウト設定
        )
        
        # ファイル存在確認とサイズ取得
        file_exists = os.path.exists(png_file)
        file_size = os.path.getsize(png_file) if file_exists else None
        
        # コマンドが失敗した場合（終了コードが0以外）
        if result.returncode != 0:
            error_message = f"mmdc command failed with return code {result.returncode}\nUsed mmdc path: {mmdc_path}"
            if result.stderr:
                error_message += f"\nSTDERR: {result.stderr}"
            
            result_data = {
                "status": "fail",
                "mermaid_script_file": mmd_file if os.path.exists(mmd_file) else None,
                "diagram_file": png_file if file_exists else None,
                "file_exists": file_exists,
                "file_size": file_size,
                "error": error_message,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "command_output": f"Used mmdc path: {mmdc_path}\nSTDOUT:\n{result.stdout or ''}\nSTDERR:\n{result.stderr or ''}"
            }
            return json.dumps(result_data, ensure_ascii=False)
        
        # 成功時のJSON戻り値
        result_data = {
            "status": "success",
            "mermaid_script_file": mmd_file,
            "diagram_file": png_file,
            "file_exists": file_exists,
            "file_size": file_size,
            "error": None,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "command_output": f"Used mmdc path: {mmdc_path}\nSTDOUT:\n{result.stdout or ''}\nSTDERR:\n{result.stderr or ''}"
        }
        return json.dumps(result_data, ensure_ascii=False)
        
    except Exception as e:
        # その他の例外
        error_message = f"Unexpected error during diagram generation: {str(e)}"
        print(error_message)
        
        # ファイル存在確認
        file_exists = os.path.exists(png_file) if 'png_file' in locals() else False
        file_size = os.path.getsize(png_file) if file_exists else None
        
        result_data = {
            "status": "fail", 
            "mermaid_script_file": mmd_file if os.path.exists(mmd_file) else None,
            "diagram_file": png_file if file_exists else None,
            "file_exists": file_exists,
            "file_size": file_size,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "command_output": error_message
        }
        return json.dumps(result_data, ensure_ascii=False)

custom_code_block_tags = ("'''python", "'''")
agent = CodeAgent(
    tools=[get_mermaid_script_guidelines_tool, generate_mermaid_diagram_tool],  
    model=model,
    use_structured_outputs_internally=False,
    max_steps=10,
    code_block_tags=custom_code_block_tags,
    additional_authorized_imports=["json"],
    stream_outputs=True
)

def process_user_message_with_agent(user_message):
    if not user_message.strip():
        return "システム要件を入力してください。", "ステータス: 入力待ち", "", "", None, ""
    
    try:   
        task_prompt = f"""
        ユーザーメッセージ：{user_message}
        """
        result = agent.run(
            task=task_prompt,
            reset=True,  # 会話をリセット
            max_steps=10   # 最大3ステップで制限
        )
        
        # agent.runの戻り値からファイルパス名を抽出
        result_str = str(result)
        
        # JSON形式の結果があるかチェック
        import json
        
        # JSONパターンを検索
        json_pattern = r'\{[^}]*"status"[^}]*\}'
        json_matches = re.findall(json_pattern, result_str)
        
        mermaid_script_file_from_json = None
        for json_str in json_matches:
            try:
                json_data = json.loads(json_str)
                # ツールのJSONに mermaid_script_file が含まれていれば保持
                if not mermaid_script_file_from_json and "mermaid_script_file" in json_data:
                    mermaid_script_file_from_json = json_data.get("mermaid_script_file") or None
            except:
                continue
        
        # エージェントの応答は純粋な結果文字列を使用
        response_text = result_str
        
        # outputディレクトリ内の.pngファイルのパスを検索
        png_pattern = r'output[/\\]mermaid_diagram_\d{8}_\d{6}\.png'
        
        png_match = re.search(png_pattern, result_str)
        
        if png_match:
            image_file = png_match.group(0)
            # スクリプトファイルはツールのJSONを優先
            script_file = mermaid_script_file_from_json if mermaid_script_file_from_json else ""
            
            if os.path.exists(image_file):
                generated_image = Image.open(image_file)
                
                script_content = ""
                if script_file and os.path.exists(script_file):
                    try:
                        with open(script_file, 'r', encoding='utf-8') as f:
                            script_content = f.read()
                    except Exception as e:
                        script_content = f"スクリプトファイル読み込みエラー: {str(e)}"
                
                # スクリプトファイルがJSONに無い場合はステータスへ追記
                status_text = "ダイアグラムが正常に生成されました。"
                if not script_file:
                    status_text += " スクリプトファイルは生成されていません"
                return (
                    response_text,
                    status_text,
                    script_file,
                    image_file,
                    generated_image,
                    script_content
                )
            else:
                return (
                    response_text,
                    f"エラー: 画像ファイルが存在しません。",
                    script_file,
                    image_file,
                    None,
                    ""
                )
        else:
            # ファイルパスが見つからない場合
            return (
                response_text,
                f"警告: ツール実行結果からファイルパスを特定できませんでした。",
                "",
                "",
                None,
                ""
            )
        
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", f"エラーステータス: {type(e).__name__}", "", "", None, ""

def clear_all():
    return "", "", "", "", "", None, ""

with gr.Blocks(title="システム設計支援エージェント") as interface:
    gr.Markdown("# システム設計支援エージェント")
    
    with gr.Row():
        with gr.Column():
            user_message = gr.Textbox(
                label="要件入力",
                placeholder="システム要件を入力してください...",
                lines=10,
                max_lines=10,
                show_copy_button=True
            )
            with gr.Row():
                send_btn = gr.Button("送信", variant="primary")
                clear_btn = gr.Button("クリア", variant="secondary")
            
        with gr.Column():
            
            result_output = gr.Textbox(
                label="エージェントの応答",
                lines=5,
                max_lines=25,
                show_copy_button=True
            )
            status_output = gr.Textbox(
                label="ステータス",
                lines=1,
                max_lines=1,
                show_copy_button=True
            )
            with gr.Accordion("成果物", open=False):
                script_file_output = gr.Textbox(
                    label="スクリプトファイル名",
                    lines=1,
                    max_lines=1,
                    show_copy_button=True
                )
                image_file_output = gr.Textbox(
                    label="画像ファイル名",
                    lines=1,
                    max_lines=1,
                    show_copy_button=True
                )
                script_output = gr.Textbox(
                    label="生成されたスクリプト",
                    lines=25,
                    max_lines=25,
                    show_copy_button=True
                )
    
    with gr.Row():
        image_output = gr.Image(
            label="ダイアグラム",
            type="pil",
            height=1024,
            show_download_button=True
        )
    
    send_btn.click(
        fn=process_user_message_with_agent,
        inputs=[user_message],
        outputs=[result_output, status_output, script_file_output, image_file_output, image_output, script_output]
    )
    
    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[user_message, result_output, status_output, script_file_output, image_file_output, image_output, script_output]
    )

interface.launch(share=False)
