import streamlit as st
import os
import json
import time

try:
    from google import genai
    from google.genai import types
    HAS_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    HAS_NEW_SDK = False

st.set_page_config(page_title="AI Video Studio (Google Flow)", page_icon="🎬", layout="wide")

st.title("🎬 AI Video Studio (Powered by Google Flow)")
st.markdown("Biến ý tưởng của bạn thành hình ảnh và video điện ảnh sử dụng hệ sinh thái AI của Google (Gemini, NanoBanana 2, Veo 3.1).")

# Sidebar cấu hình
with st.sidebar:
    st.header("⚙️ Cài đặt API")
    api_key_input = st.text_input("Nhập Google Gemini API Key:", type="password", help="Lấy API Key miễn phí tại aistudio.google.com")
    st.markdown("---")
    st.markdown("""
    **Quy trình hoạt động:**
    1. Lên kịch bản bằng Gemini
    2. Vẽ ảnh bằng NanoBanana 2
    3. Tạo video bằng Google Flow (Veo 3.1)
    """)

# Main Content
idea = st.text_area("💡 Nhập ý tưởng video của bạn:", placeholder="Ví dụ: Một chú chó phi hành gia đang đi dạo trên bề mặt sao hỏa, phong cách điện ảnh sắc nét...")

if st.button("🚀 Bắt đầu tạo Video", type="primary"):
    if not idea:
        st.warning("Vui lòng nhập ý tưởng của bạn!")
    elif not api_key_input:
        st.error("Vui lòng nhập Google Gemini API Key ở thanh bên trái!")
    else:
        st.success("Đã nhận lệnh! Bắt đầu quy trình tự động...")
        
        # 1. Gọi Gemini API
        with st.status("🧠 Đang phân tích ý tưởng và lên kịch bản...", expanded=True) as status:
            try:
                system_prompt = """
                Bạn là chuyên gia sáng tạo kịch bản video.
                Người dùng đưa ra ý tưởng, bạn trả về DUY NHẤT một chuỗi JSON gồm:
                {
                    "title": "Tiêu đề video",
                    "script": "Kịch bản/lời thoại",
                    "image_prompt": "Prompt tiếng Anh cực kỳ chi tiết dùng để vẽ ảnh",
                    "video_prompt": "Prompt tiếng Anh chi tiết dùng để tạo video"
                }
                """
                
                if HAS_NEW_SDK:
                    client = genai.Client(api_key=api_key_input)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[system_prompt, f"Ý tưởng: {idea}"],
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    result_text = response.text
                else:
                    genai.configure(api_key=api_key_input)
                    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt, generation_config={"response_mime_type": "application/json"})
                    response = model.generate_content(f"Ý tưởng: {idea}")
                    result_text = response.text
                    
                concept = json.loads(result_text)
                
                st.markdown(f"**Tiêu đề:** {concept.get('title')}")
                st.markdown(f"**Kịch bản:** {concept.get('script')}")
                status.update(label="✅ Phân tích xong kịch bản!", state="complete", expanded=False)
                
            except Exception as e:
                st.error(f"Lỗi khi lên kịch bản: {e}")
                status.update(label="❌ Lỗi phân tích", state="error")
                st.stop()

        # 2. Tạo ảnh bằng NanoBanana 2
        with st.status("🎨 Đang vẽ ảnh tham chiếu bằng NanoBanana 2...", expanded=True) as status:
            try:
                image_prompt = concept.get("image_prompt", "")
                image_path = "output_image.jpg"
                
                if HAS_NEW_SDK:
                    client = genai.Client(api_key=api_key_input)
                    # Thử sử dụng mô hình tạo ảnh chuẩn của Google (Imagen 3)
                    response = client.models.generate_content(
                        model='imagen-3.0-generate-001', 
                        contents=image_prompt,
                        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                    )
                    part = response.candidates[0].content.parts[0]
                    if hasattr(part, 'inline_data') and part.inline_data:
                        with open(image_path, "wb") as f:
                            f.write(part.inline_data.data)
                        st.image(image_path, caption="Ảnh tham chiếu do AI tạo")
                        status.update(label="✅ Vẽ ảnh xong!", state="complete", expanded=False)
                    else:
                        raise Exception("Không nhận được dữ liệu ảnh.")
                else:
                    status.update(label="⚠️ API cũ không hỗ trợ tạo ảnh trực tiếp ở đây, bỏ qua bước tạo ảnh.", state="complete")
                    
            except Exception as e:
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    st.warning("⚠️ Tài khoản của bạn chưa được Google cấp quyền dùng model vẽ ảnh này (hoặc cần nạp tiền). Bỏ qua bước tạo ảnh.")
                else:
                    st.warning(f"Lỗi khi vẽ ảnh: {e}. Hệ thống sẽ tiếp tục tạo video.")
                status.update(label="⚠️ Vẽ ảnh thất bại (Bỏ qua)", state="error")

        # 3. Tạo Video bằng Google Flow / Veo 3.1
        with st.status("🎥 Đang render Video bằng Google Flow (Veo 3.1)... Quá trình này mất khoảng 1-2 phút", expanded=True) as status:
            try:
                video_prompt = concept.get("video_prompt", "")
                video_path = "output_video.mp4"
                
                if HAS_NEW_SDK:
                    client = genai.Client(api_key=api_key_input)
                    st.write("Đang gửi yêu cầu lên máy chủ Google...")
                    operation = client.models.generate_videos(
                        model="veo-3.1-generate-preview",
                        prompt=video_prompt,
                        config=types.GenerateVideosConfig(aspect_ratio="16:9", duration_seconds=8)
                    )
                    
                    while not operation.done:
                        st.write("⏳ Đang render... Vui lòng đợi...")
                        time.sleep(20)
                        operation = client.operations.get(operation)
                        
                    st.write("Đang tải video về máy...")
                    generated_video = operation.response.generated_videos[0]
                    
                    try:
                        client.files.download(file=generated_video.video)
                        generated_video.video.save(video_path)
                    except Exception:
                        if hasattr(generated_video.video, 'uri'):
                            import requests
                            r = requests.get(generated_video.video.uri)
                            with open(video_path, 'wb') as f:
                                f.write(r.content)
                                
                    st.video(video_path)
                    status.update(label="✅ Video đã sẵn sàng!", state="complete", expanded=True)
                    
                else:
                    st.error("SDK phiên bản cũ không hỗ trợ tạo video. Cần nâng cấp google-genai.")
                    status.update(label="❌ Lỗi Video", state="error")
                    
            except Exception as e:
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    st.error("⚠️ Tài khoản Google AI Studio của bạn chưa được cấp quyền dùng Veo 3.1 (Google Flow). Tính năng này thường yêu cầu tài khoản được duyệt riêng hoặc phải thêm thẻ thanh toán (Billing).")
                else:
                    st.error(f"Lỗi khi tạo video: {e}")
                status.update(label="❌ Render Video thất bại", state="error")

        st.balloons()
        st.success("🎉 Hoàn tất toàn bộ quy trình! Bạn có thể xem kết quả ở trên.")
