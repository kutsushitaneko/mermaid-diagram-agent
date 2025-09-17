import datetime
import os
import re
from PIL import Image
import subprocess
import shutil
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, tool, MCPClient, REMOVE_PARAMETER
from mcp import StdioServerParameters
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
    stop=REMOVE_PARAMETER, 
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
    マーメイドダイアグラムの画像ファイルを生成するツール（例外処理版）。
    
    Args:
        mermaid_script: ダイアグラムを生成するためのマーメイドスクリプト
        
    Returns:
        str: 生成されたPNGファイルのパス
        
    Raises:
        ValueError: 入力パラメータが無効な場合
        RuntimeError: ダイアグラム生成に失敗した場合
        FileNotFoundError: mmdc コマンドが見つからない場合
    
    Example usage:
        try:
            diagram_path = generate_mermaid_diagram_tool(mermaid_script)
            # diagram_path を使用して処理を続行
        except Exception as e:
            print(f"ダイアグラム生成失敗: {e}")
    """
    
    if not mermaid_script or not mermaid_script.strip():
        raise ValueError("mermaid_script is required and cannot be empty")
    
    # outputディレクトリの作成
    output_dir = "output"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create output directory: {str(e)}")
    
    # ファイル名生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mmd_file = f"{output_dir}/mermaid_diagram_{timestamp}.mmd"
    png_file = f"{output_dir}/mermaid_diagram_{timestamp}.png"
    
    # スクリプトファイル書き込み
    try:
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_script)
    except Exception as e:
        raise RuntimeError(f"Failed to write mermaid script file: {str(e)}")
    
    # mmdc コマンド確認
    mmdc_path = shutil.which("mmdc")
    if mmdc_path is None:
        raise FileNotFoundError("mmdc command not found. Install with: npm install -g @mermaid-js/mermaid-cli")
    
    # ダイアグラム生成
    try:
        result = subprocess.run(
            [mmdc_path, '-i', mmd_file, '-o', png_file, '--width', '2048', '--height', '2048'],
            capture_output=True,
            text=True,
            shell=False,
            encoding='utf-8',
            timeout=60
        )
        
        if result.returncode != 0:
            error_msg = f"mmdc failed (exit code {result.returncode})"
            if result.stderr:
                # 制御文字を除去してエラーメッセージを安全に
                clean_stderr = result.stderr.strip().replace('\n', ' ').replace('\r', ' ')
                error_msg += f": {clean_stderr}"
            raise RuntimeError(error_msg)
        
        if not os.path.exists(png_file):
            raise RuntimeError("Diagram file was not created")
        
        return png_file
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Diagram generation timed out (60 seconds)")
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise  # RuntimeErrorは再発生
        raise RuntimeError(f"Unexpected error during diagram generation: {str(e)}")

# SQLcl MCPクライアントの設定
sqlcl_server_parameters = StdioServerParameters(
    command="D:\\tools\\sqlcl\\bin\\sql.exe",
    args=["-mcp"],
)
sqlcl_mcp_client = MCPClient(
    server_parameters=sqlcl_server_parameters,
    structured_output=False
)
sqlcl_tools = sqlcl_mcp_client.get_tools()

agent = CodeAgent(
    tools=[get_mermaid_script_guidelines_tool, generate_mermaid_diagram_tool, *sqlcl_tools],  
    model=model,
    use_structured_outputs_internally=False,
    max_steps=10,
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
            reset=False,  # 会話をリセットするかどうか。リセットする場合はTrue、しない場合はFalse
            max_steps=10   # 最大10ステップで制限
        )
        
        # agent.runの戻り値からファイルパス名を抽出
        result_str = str(result)
        
        # エージェントの応答は純粋な結果文字列を使用
        response_text = result_str

        # CodeAgent の戻り値テキストから .png パスを抽出し、拡張子置換で .mmd を導出（ディレクトリ探索はしない）
        png_pattern = r'output[/\\]mermaid_diagram_\d{8}_\d{6}\.png'

        png_match = re.search(png_pattern, result_str)

        if png_match:
            image_file = png_match.group(0)
            # mmd は result には含まれないため、png の拡張子を置換して導出
            script_file = re.sub(r'\.png$', '.mmd', image_file)

            if os.path.exists(image_file):
                generated_image = Image.open(image_file)

                script_content = ""
                if script_file and os.path.exists(script_file):
                    try:
                        with open(script_file, 'r', encoding='utf-8') as f:
                            script_content = f.read()
                    except Exception as e:
                        script_content = f"スクリプトファイル読み込みエラー: {str(e)}"

                status_text = "ダイアグラムが正常に生成されました。"
                if not script_file:
                    status_text += " スクリプトファイルが見つかりません。"

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
                    f"エラー: 画像ファイル '{image_file}' が存在しません。",
                    script_file if 'script_file' in locals() else "",
                    image_file,
                    None,
                    ""
                )
        else:
            # 画像ファイルの記載がエージェント応答に無い場合はテキスト応答を返す
            return (
                response_text,
                "タスク完了: テキスト応答",
                "",
                "",
                None,
                ""
            )
        
    except Exception as e:
        error_msg = f"エラーが発生しました: {str(e)}"
        status_msg = f"エラーステータス: {type(e).__name__}"
        return error_msg, status_msg, "", "", None, ""

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