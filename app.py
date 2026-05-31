import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="VeriIjazah AI", page_icon="🎓", layout="wide")

st.title("🎓 VeriIjazah AI")
st.markdown("""
**Solusi Pertahanan Pertama (First-line of Defense) Verifikasi Dokumen Akademik**

Aplikasi ini menggunakan teknologi AI tingkat lanjut (Gemini 1.5 Flash) untuk melakukan dekonstruksi elemen visual, uji konsistensi logika, dan mendeteksi anomali (bekas editan) pada ijazah.
""")

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Konfigurasi")
api_key = st.sidebar.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
if not api_key:
    st.sidebar.warning("Silakan masukkan Gemini API Key Anda untuk mulai menggunakan aplikasi.")
    st.stop()

# Initialize Gemini
genai.configure(api_key=api_key)

generation_config = {
  "temperature": 0.1,
  "top_p": 1,
  "top_k": 32,
  "max_output_tokens": 4096,
  "response_mime_type": "application/json",
}

# The prompt instructions
SYSTEM_PROMPT = """
Anda adalah Inspektur Forensik Digital spesialis dalam verifikasi dokumen akademik (Ijazah).
Tugas Anda adalah menganalisis gambar ijazah yang diberikan dan mengembalikan hasil analisis dalam format JSON murni.

Lakukan tiga lapis analisis berikut secara mendalam:

1. **Ekstraksi Data (OCR Terarah):**
   Ambil data-data krusial:
   - Nama Lengkap
   - Nomor Induk Mahasiswa (NIM) atau Nomor Pokok Mahasiswa (NPM)
   - Universitas / Institusi
   - Program Studi / Fakultas
   - Tanggal Kelulusan / Tanggal Terbit
   - Nomor Seri Ijazah (Biasanya ada di pojok atas atau bawah)
   - Nama Dekan / Rektor yang menandatangani

2. **Logic Consistency Check (Uji Konsistensi Logika):**
   Bandingkan pola data satu sama lain.
   - Apakah tahun pada Nomor Seri sesuai dengan Tahun Kelulusan? (Contoh: NIM angkatan 2020 biasanya lulus 2024. Nomor seri yang mengandung tahun harus sinkron).
   - Apakah format NIM wajar untuk tingkat universitas?
   - Jika ada kejanggalan logika, sebutkan secara spesifik.

3. **Visual Anomaly Detection (Deteksi Anomali Visual):**
   Sebagai AI Multimodal tingkat piksel, periksa gambar secara teliti untuk mencari indikasi manipulasi (editan Photoshop/Overlay):
   - *Cloning Artifacts*: Adanya pola piksel atau noise yang berulang tak wajar.
   - *Font Misalignment*: Ketidakselarasan font, jenis huruf yang tiba-tiba berbeda di area krusial (seperti Nama atau NIM).
   - *Background Noise*: Perbedaan tekstur, kecerahan, atau *noise* di sekitar teks dibandingkan latar belakang kertas aslinya (indikasi tambal sulam).
   - *Tanda Tangan & Stempel*: Apakah stempel terlihat natural menimpa kertas dan teks, atau terlihat seperti gambar PNG transparan yang ditempel?

Keluarkan analisis Anda murni dalam bentuk JSON dengan skema berikut:
{
  "status_kesimpulan": "ASLI" atau "INDIKASI PALSU",
  "confidence_score": 0-100,
  "ekstraksi_data": {
    "nama": "...",
    "nim": "...",
    "universitas": "...",
    "program_studi": "...",
    "tanggal_lulus": "...",
    "nomor_seri": "...",
    "penandatangan": "..."
  },
  "logic_consistency": {
    "status": "Aman" atau "Peringatan",
    "catatan": ["catatan 1", "catatan 2"]
  },
  "visual_anomaly": {
    "status": "Aman" atau "Peringatan",
    "catatan": ["catatan 1", "catatan 2"]
  },
  "penjelasan_teknis": "Penjelasan ringkas mengapa Anda mengambil kesimpulan tersebut."
}
"""

def analyze_document(image):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    # Using JSON format helps us parse it consistently
    response = model.generate_content([SYSTEM_PROMPT, image])
    return response.text

# --- Main Area ---
st.subheader("📤 Unggah Dokumen Ijazah")
uploaded_file = st.file_uploader("Format yang didukung: JPG, JPEG, PNG", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display image
    image = Image.open(uploaded_file)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(image, caption="Dokumen yang diunggah", use_column_width=True)
    
    with col2:
        if st.button("🔍 Mulai Audit Forensik", type="primary", use_container_width=True):
            with st.spinner("Menganalisis dokumen pada tingkat piksel dan semantik..."):
                try:
                    result_json = analyze_document(image)
                    
                    try:
                        data = json.loads(result_json)
                        
                        # --- Display Results ---
                        st.subheader("📊 Laporan Forensik")
                        
                        status = data.get("status_kesimpulan", "TIDAK DIKETAHUI")
                        if status == "ASLI":
                            st.success(f"### Status: {status} (Skor Keyakinan: {data.get('confidence_score')}%)")
                        else:
                            st.error(f"### Status: {status} (Skor Keyakinan: {data.get('confidence_score')}%)")
                            
                        st.info(f"**Penjelasan Teknis:** {data.get('penjelasan_teknis')}")
                        
                        # Extraction Tab
                        tab1, tab2, tab3 = st.tabs(["📝 Ekstraksi Data", "🧠 Logic Check", "👁️ Visual Anomaly"])
                        
                        with tab1:
                            st.json(data.get("ekstraksi_data", {}))
                            
                        with tab2:
                            logic = data.get("logic_consistency", {})
                            if logic.get("status") == "Aman":
                                st.success("✅ Tidak ditemukan anomali logis.")
                            else:
                                st.warning("⚠️ Ditemukan anomali logis:")
                                for cat in logic.get("catatan", []):
                                    st.write(f"- {cat}")
                                    
                        with tab3:
                            visual = data.get("visual_anomaly", {})
                            if visual.get("status") == "Aman":
                                st.success("✅ Tidak ada tanda manipulasi gambar (Editan/Cloning).")
                            else:
                                st.error("🚨 Ditemukan jejak manipulasi visual:")
                                for cat in visual.get("catatan", []):
                                    st.write(f"- {cat}")
                                    
                    except json.JSONDecodeError:
                        st.error("Gagal membaca hasil dari AI. Output tidak berformat JSON.")
                        st.write("Output AI:", result_json)
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghubungi API Gemini: {str(e)}")
