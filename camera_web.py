import streamlit as st
import math
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib as mpl
import io
import base64
import numpy as np

st.markdown(
    """
    <style>
      /* 1. 讓主區塊不設 max-width 並允許橫向捲動 */
      div[role="main"] .block-container {
        max-width: none !important;
        overflow-x: auto;
      }
      /* 2. 取消所有 <img> 的 max-width 限制 */
      img {
        max-width: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# 指定一个支持 Emoji 的字体
mpl.rcParams['font.family'] = 'Segoe UI Emoji'

st.title("📷 Face Recognition Calculator")

# 基礎輸入
h_res = st.number_input("Horizontal resolution (pixels)", min_value=1)
v_res = st.number_input("Vertical resolution (pixels)", min_value=1)

sw_in = st.text_input("Sensor width (mm) [Leave blank if unknown]")
ps_in = st.text_input("Pixel size (µm) [Leave blank if unknown]")

# 計算 sensor width 或 pixel size
sensor_width = None
pixel_size = None
if sw_in:
    sensor_width = float(sw_in)
    pixel_size = sensor_width / h_res * 1000
    st.write(f"Pixel size: **{pixel_size:.2f} µm**")
elif ps_in:
    pixel_size = float(ps_in)
    sensor_width = h_res * (pixel_size / 1000)
    st.write(f"Sensor width: **{sensor_width:.2f} mm**")
else:
    st.warning("Please provide either Sensor width or Pixel size")

# 進一步計算
if sensor_width and pixel_size:
    sensor_height = (pixel_size / 1000) * v_res

    # --- Optical Format 計算 ---
    diag_mm = math.hypot(sensor_width, sensor_height)
    opt_inch = diag_mm * 1.5 / 25.4
    # film (35mm) optical-format-inches
    film_diag = math.hypot(36, 24)
    film_inch = film_diag * 1.5 / 25.4
    formats = [
        ("1/4″",       1/4),
        ("1/3.6″",     1/3.6),
        ("1/3.5″",     1/3.5),
        ("1/3.2″",     1/3.2),
        ("1/3″",       1/3),
        ("1/2.8″",     1/2.8),
        ("1/2.7″",     1/2.7),
        ("1/2.5″",     1/2.5),
        ("1/2″",       1/2),
        ("1/1.8″",     1/1.8),
        ("2/3″",       2/3),
        ("1″",         1.0),
        ("4/3″",       4/3),
        ("35mm",       film_inch),
    ]
    optical_format = min(formats, key=lambda x: abs(opt_inch - x[1]))[0]

    choice = st.radio("Input Method", ["Focal length (mm)", "Diagonal FOV (°)"])

    focal_length = None
    if choice == "Focal length (mm)":
        focal_length = st.number_input("Focal length (mm)", min_value=0.0)
        if focal_length > 0:
            hfov_deg = 2 * math.degrees(math.atan(sensor_width / (2 * focal_length)))
            diagonal = math.hypot(sensor_width, sensor_height)
            dfov_deg = 2 * math.degrees(math.atan(diagonal / (2 * focal_length)))
            st.write(f"Horizontal FOV: **{hfov_deg:.2f}°**")
            st.write(f"Diagonal FOV: **{dfov_deg:.2f}°**")
    else:
        dfov_deg = st.number_input("Diagonal FOV (°)", min_value=0.0)
        if dfov_deg > 0:
            diagonal = math.hypot(sensor_width, sensor_height)
            focal_length = (diagonal / 2) / math.tan(math.radians(dfov_deg) / 2)
            st.write(f"Focal length: **{focal_length:.2f} mm**")

    if focal_length and focal_length > 0:
        mode = st.radio("Select Calculation", ["Distance (cm)", "Horizontal FOV (cm)"])

        if mode == "Distance (cm)":
            distance_cm = st.number_input("Distance (cm)", min_value=0.0)
            if distance_cm > 0:
                distance_mm = distance_cm * 10
                m = focal_length / (distance_mm - focal_length)
                hfov_mm = sensor_width / m
                hfov_cm = hfov_mm / 10
                st.write(f"Horizontal FOV: **{hfov_cm:.2f} cm**")
        else:
            hfov_cm = st.number_input("Horizontal FOV (cm)", min_value=0.0)
            if hfov_cm > 0:
                hfov_mm = hfov_cm * 10
                m = sensor_width / hfov_mm
                distance_mm = focal_length / m + focal_length
                distance_cm = distance_mm / 10
                st.write(f"distance: **{distance_cm:.2f} cm**")

        if 'hfov_mm' in locals():
            mm_per_px = hfov_mm / h_res
            cm_per_px = mm_per_px / 10
            st.write(f"Each pixel covers: **{cm_per_px:.4f} cm**")

            px_for_18cm = 18.0 / cm_per_px
            st.write(f"18 cm wide object ≈ **{px_for_18cm:.0f} pixels**")

            pixel_size_fr_cm = 18.0 / 80.0
            hfov_fr_cm = pixel_size_fr_cm * h_res
            hfov_fr_mm = hfov_fr_cm * 10
            distance_fr_mm = focal_length / (sensor_width / hfov_fr_mm) + focal_length
            distance_fr_cm = distance_fr_mm / 10

            st.write("### Face Recognition 18 cm / 80 pixels Scenario")
            st.write(f"- Pixel size: **{pixel_size_fr_cm:.3f} cm/px**")
            st.write(f"- Horizontal FOV: **{hfov_fr_cm:.2f} cm**")
            st.write(f"- Required distance: **{distance_fr_cm:.2f} cm**")


            # --- System Diagram & Parameters with Face-Recognition Metrics ---
            st.write("### System Diagram")
            st.image("optical_diagram.png", use_container_width=True)
            
            # 兩欄：左參數，右 Face‐Recognition 特殊指標
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### Current System")
                st.markdown(f"""

            **Working Distance:** {distance_cm:.2f} cm  
            **Horizontal FOV (HFOV):** {hfov_mm/10:.2f} cm  
            **Diagonal FOV (DFOV):** {dfov_deg:.2f}°  
            **Focal Length:** {focal_length:.2f} mm  
            **Sensor Size:** {sensor_width:.2f} mm × {sensor_height:.2f} mm  
            **Optical Format:** {optical_format}  
            **Active Pixels:** {h_res} (H) × {v_res} (V) = {h_res * v_res / 1_000_000:.1f} MP
            """)
            
            with col2:
                st.markdown("##### Face Recognition–Compliant System")
                st.markdown(f"""
            **Required Distance:** {distance_fr_cm:.2f} cm  
            **Required HFOV:** {hfov_fr_cm:.2f} cm  
            """)

            
            # 簡化版電池條狀圖
            st.write("### Visual Indicator (Assume 18cm wide face)")

            fig, ax = plt.subplots(figsize=(6, 1.5))
            max_px = 80.0
            fill_px = min(px_for_18cm, max_px)            # 條狀圖最多填到 80px
            actual_ratio = px_for_18cm / max_px * 100     # 真正的占比，可能超過 100%

            # 畫出綠色填滿部分
            ax.barh(0, fill_px, color="green")
            # 畫出剩餘部分（灰色）
            ax.barh(0, max_px - fill_px, left=fill_px, color="lightgray")

            ax.set_xlim(0, max_px)
            ax.set_yticks([])
            ax.set_xticks([])

            # 標題顯示 真實 px 和 真實占比（可能 >100%）
            ax.set_title(
                f"Face Width Occupancy: {px_for_18cm:.1f} px / {max_px:.0f} px "
                f"({actual_ratio:.1f}% )"
            )

            st.pyplot(fig)
            
            
            # --- Real Face Pixelation Comparison ---
            st.write("### Face Clarity Comparison")
            uploaded = st.file_uploader("Upload a face image to visualize pixelation", type=['png','jpg','jpeg'])
            if uploaded is not None:
                # 讀取並裁切正方形
                img = Image.open(uploaded)
                w, h = img.size
                m = min(w, h)
                img = img.crop(((w-m)//2, (h-m)//2, (w+m)//2, (h+m)//2))

                # 產生像素化版本
                def pixelate(im, px):
                    small = im.resize((int(px), int(px)), resample=Image.BILINEAR)
                    return small.resize((256,256), resample=Image.NEAREST)

                col1, col2 = st.columns(2)
                with col1:
                    st.image(pixelate(img, px_for_18cm), caption=f"Computed: {px_for_18cm:.0f} px", use_container_width=True)
                with col2:
                    st.image(pixelate(img, 80), caption="Required: 80 px", use_container_width=True)

            # --- Depth of Field Calculator ---
            st.write("### Depth of Field Calculator")

            # 必填參數
            f_number      = st.number_input("Aperture (f-number)", min_value=0.1, value=2.0)
            focus_dist_cm = st.number_input("Focus at the subject distance (cm)", min_value=0.0, value=100.0)

            # 先計算 CoC，不再讓使用者手動輸入
            if focal_length and f_number > 0 and focus_dist_cm > 0 and pixel_size:
                # 1. Airy disk (μm)
                λ = 0.55
                D_airy = 2.44 * λ * f_number
                # 2. Pixel pitch (μm)
                Ppix = pixel_size
                # 3. Permissible δ
                delta = max(D_airy, Ppix)
                # 4. Bayer factor
                C_min = delta * 2 #留著之後可能用的到
                C_max = delta * 3
                # 顯示所有中間值
                st.write(f"Airy disk: **{D_airy:.3f} μm**")
                st.write(f"Pixel pitch: **{Ppix:.3f} μm**")
                st.write(f"Circle of Confusion (min): **{C_min/1000:.5f} mm**")
                # 最終 CoC 以最小值當預設
                C = C_min / 1000  # mm

                # 單位轉換
                f = focal_length           # mm
                N = f_number
                u = focus_dist_cm * 10     # mm

                # 計算 Hyperfocal Distance H
                H = f + (f * f) / (N * C)

                # 計算 Near Focus Distance Dn
                Dn = (H * u) / (H + (u - f))

                # 計算 Far Focus Distance Df
                if u < H:
                    Df = (H * u) / (H - (u - f))
                else:
                    Df = float('inf')

                # 計算 Depth of Field
                DoF = float('inf') if Df == float('inf') else (Df - Dn)

                # 以公尺顯示
                st.write(f"**Hyperfocal Distance:** {H/1000:.3f} m")
                st.write(f"**Near Focus Distance:** {Dn/1000:.3f} m")
                st.write(f"**Far Focus Distance:** {'∞' if Df==float('inf') else f'{Df/1000:.3f} m'}")
                st.write(f"**Depth of Field (DoF):** {'∞' if DoF==float('inf') else f'{DoF/1000:.3f} m'}")

                # --- Depth of Field Plot (左右上下都固定) --- 
                # 1) 先把参数都算好
                near_cm    = Dn    / 10
                subject_cm = u     / 10
                far_cm_raw = Df    / 10 if Df != float('inf') else float('inf')
                max_plot_cm = 1500
                far_cm      = min(far_cm_raw, max_plot_cm)

                # 2) 建图并让 Axes 铺满整个 Figure
                fig = plt.figure(figsize=(60, 4), dpi=300)
                ax  = fig.add_axes([0, 0, 1, 1])
                ax.axis('off')

                # 3) 锁定并取消所有 margin
                ax.set_autoscale_on(False)
                ax.set_xlim(0, max_plot_cm)
                ax.set_ylim(0, 1)
                ax.margins(x=0, y=0)        # 彻底关掉 x/y 轴 padding
                ax.set_xbound(0, max_plot_cm)
                ax.set_ybound(0, 1)

                # 4) 背景 & DoF span 用 x–轴变换，y 从 0→1
                ax.axvspan(
                    0, max_plot_cm,
                    ymin=0, ymax=1,
                    transform=ax.get_xaxis_transform(),
                    color='lightblue', alpha=0.2,
                    zorder=0
                )
                ax.axvspan(
                    near_cm, far_cm,
                    ymin=0, ymax=1,
                    transform=ax.get_xaxis_transform(),
                    color='lightblue', alpha=0.8,
                    zorder=1
                )

                # 5) 相机标记 → 完全用 axes fraction
                ax.text(
                    0, 0.5, '📷 Camera',
                    transform=ax.transAxes,
                    ha='left', va='center', fontsize=14,
                    clip_on=True
                )

                # 6) 焦点目标 → x 用 data, y 用 axes fraction
                ax.plot(subject_cm, 0.5, 'ro', clip_on=True)
                ax.text(
                    subject_cm, 0.6, f'🎯 Focus Target\n{subject_cm:.1f} cm',
                    transform=ax.get_xaxis_transform(),
                    ha='center', va='bottom', fontsize=14, color='red',
                    clip_on=True
                )

                # 7) Near / Far 注记也是 x–data, y–axes
                ax.text(
                    near_cm, 0.05, f'Near\n {near_cm:.1f} cm',
                    transform=ax.get_xaxis_transform(),
                    ha='center', va='bottom', fontsize=12, fontweight='bold',
                    clip_on=True
                )
                if Df != float('inf'):
                    display_far = (
                        f'{far_cm:.1f} cm'
                        if far_cm_raw <= max_plot_cm
                        else f'{Df/1000:.1f} m'
                    )
                    x_label = max(far_cm - 10, 0) 
                    ax.text(
                        x_label, 0.05, f'Far\n {display_far}',
                        transform=ax.get_xaxis_transform(),
                        ha='center', va='bottom', fontsize=12, fontweight='bold',
                        clip_on=True
                    )
                    if Df < max_plot_cm*10: #換成mm
                        ax.text(
                        1.0, 0.05, 'infinity',
                        transform=ax.transAxes,    # x=1.0 对应 axes 右边缘
                        ha='right', va='bottom',
                        fontsize=12, fontweight='bold',
                        clip_on=True
                        )
                else:
                    ax.text(
                        1, 0.05, 'Far\n infinity',
                        transform=ax.transAxes,
                        ha='right', va='bottom', fontsize=12, fontweight='bold',
                        clip_on=True
                    )

                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                data = base64.b64encode(buf.getvalue()).decode()

                # ← 用 HTML embed 強制 3000px 寬並顯示水平捲軸
                st.markdown(
                    f"""
                    <div style="width:100%; overflow-x:auto;">
                    <img src="data:image/png;base64,{data}"
                        style="width:3000px; max-width:none !important; display:block;" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ---------------------
                # ✅ Summary Check (fixed & reactive)
                # ---------------------
                st.subheader("✅ Summary Check")

                # --- 1. Basic Checks ---
                Dn_cm = Dn / 10
                Df_cm = (Df / 10) if Df != float('inf') else float('inf')

                min_dof_cm = st.number_input("Desired near limit (cm)", value=50.0)
                max_dof_cm = st.number_input("Desired far limit (cm)", value=1500.0)
                required_px_at_5m = st.number_input("Required face pixels at 5 m", value=80.0)

                covers = (Dn_cm <= min_dof_cm) and (Df_cm >= max_dof_cm)

                TEST_MM = 5000.0
                m5_orig = focal_length / (TEST_MM - focal_length)
                hf5_orig = sensor_width / m5_orig
                px5_orig = 18.0 / ((hf5_orig/10) / h_res)

                # 先计算实际 Near/Far 和总 DoF（cm）
                Dn_cm = Dn / 10
                Df_cm = Df / 10 if Df != float('inf') else float('inf')
                actual_total = float('inf') if Df_cm == float('inf') else Df_cm - Dn_cm

                # 然后替换原来的 covers/ misses 显示
                if covers:
                    if Df_cm == float('inf'):
                        st.success(
                            f"✅ DoF covers {min_dof_cm:.0f} cm to {max_dof_cm/100:.1f} m → "
                            f"Actual DoF: {Dn_cm:.1f} cm to ∞ (Total: ∞)"
                        )
                    else:
                        st.success(
                            f"✅ DoF covers {min_dof_cm:.0f} cm to {max_dof_cm/100:.1f} m → "
                            f"Actual DoF: {Dn_cm:.1f} cm to {Df_cm:.1f} cm (Total: {actual_total:.1f} cm)"
                        )
                else:
                    if Df_cm == float('inf'):
                        st.error(
                            f"❌ DoF misses {min_dof_cm:.0f} cm to {max_dof_cm/100:.1f} m → "
                            f"Actual DoF: {Dn_cm:.1f} cm to ∞ (Total: ∞)"
                        )
                    else:
                        st.error(
                            f"❌ DoF misses {min_dof_cm:.0f} cm to {max_dof_cm/100:.1f} m → "
                            f"Actual DoF: {Dn_cm:.1f} cm to {Df_cm:.1f} cm (Total: {actual_total:.1f} cm)"
                        )

                if px5_orig >= required_px_at_5m:
                    st.success(f"✅ At 5 m: {px5_orig:.1f} px ≥ {required_px_at_5m:.0f} px → sufficient for recognition.")
                else:
                    st.error(f"❌ At 5 m: {px5_orig:.1f} px < {required_px_at_5m:.0f} px → not sufficient for recognition.")

                if covers and px5_orig >= required_px_at_5m:
                    st.info("Current setting already meets both requirements – no adjustment needed.")
                    #st.stop()

                # --- 🔧 Adjustment Suggestions ---
                st.markdown("### 🔧 Adjustment Suggestions")

                # 1. 输入 ±范围
                N_adj = st.number_input("Aperture adjustment range + (stops)", value=2.0)
                f_adj = st.number_input("Focal length adjustment range + (mm)", value=5.0)

                # 2. 离散化 f-number & 焦距 列表
                aperture_choices = np.array([1.4,1.6,1.8,2,2.2,2.5,2.8,3.2,3.5,4,4.5,5])
                N_vals = aperture_choices[(aperture_choices >= f_number - N_adj) & (aperture_choices <= f_number + N_adj)]
                f_min = max(1.0, math.floor(focal_length - f_adj))
                f_max = math.ceil(focal_length + f_adj)
                f_vals = np.arange(f_min, f_max + 1, 1)

                # 3. 计算所有可行组合
                λ = 0.55  # μm
                cand = []
                for N_try in N_vals:
                    D_airy = 2.44 * λ * N_try
                    C_mm = 2 * max(D_airy, pixel_size) / 1000
                    for f_try in f_vals:
                        H = f_try + (f_try**2) / (N_try * C_mm)
                        u = focus_dist_cm * 10
                        Dn = (H * u) / (H + (u - f_try))
                        Df = (H * u) / (H - (u - f_try)) if u < H else float('inf')
                        ok_dof = (Dn/10 <= min_dof_cm) and ((Df/10 if Df!=float('inf') else float('inf')) >= max_dof_cm)
                        if not ok_dof:
                            continue
                        m5 = f_try / (TEST_MM - f_try)
                        px5 = 18.0 / ((sensor_width / m5 / 10) / h_res)
                        if px5 < required_px_at_5m:
                            continue
                        dN = abs(N_try - f_number) / (np.ptp(N_vals) + 1e-6)
                        dF = abs(f_try - focal_length) / (np.ptp(f_vals) + 1e-6)
                        cand.append((dN, dF, N_try, f_try))

                # 4. Guard for empty cand
                if not cand:
                    st.warning(
                        "⚠️ No valid aperture/focal length combinations found in your ± ranges. "
                        "Please widen the ranges or check your system parameters."
                    )
                    st.stop()

                # 5. 配对字典
                from collections import defaultdict
                matches_by_N = defaultdict(list)
                matches_by_f = defaultdict(list)
                for _, _, N_try, f_try in cand:
                    matches_by_N[N_try].append(f_try)
                    matches_by_f[f_try].append(N_try)

                # 6. 基础索引与滑杆范围计算
                base_idx_N = int(np.argmin(np.abs(N_vals - f_number)))
                base_idx_F = int(np.argmin(np.abs(f_vals - focal_length)))
                max_pos = len(N_vals) - 1 - base_idx_N  # 最大正方向步数
                max_neg = -(len(f_vals) - 1 - base_idx_F) # 最大负方向步数 (negative)
                slider = st.slider(
                    "Custom: ▶ move right to step f-number, ◀ move left to step focal length",
                    min_value=max_neg,
                    max_value=max_pos,
                    value=0,
                    step=1
                )

                # 7. 自定义结果展示
                if slider > 0:
                    # 右移：调整 f-number
                    idx_N = base_idx_N + slider
                    N_sel = N_vals[idx_N]
                    fls = sorted(matches_by_N.get(N_sel, []))
                    if not fls:
                        st.markdown(f"**no match when f-number = {N_sel:.1f}**")
                    else:
                        st.markdown(f"- **Aperture:** {N_sel:.1f}")
                        st.markdown(f"- **Focal Length (min):** {fls[0]:.0f} mm (+{len(fls)-1} more)")
                elif slider < 0:
                    # 左移：调整 focal length，每格 +1mm
                    steps = abs(slider)
                    idx_F = base_idx_F + steps
                    f_sel = f_vals[idx_F]
                    Ns = sorted(matches_by_f.get(f_sel, []))
                    if not Ns:
                        st.markdown(f"**no match when focal length = {f_sel:.0f} mm**")
                    else:
                        st.markdown(f"- **Focal Length:** {f_sel:.0f} mm")
                        st.markdown(f"- **Aperture (min):** {Ns[0]:.1f} (+{len(Ns)-1} more)")
                else:
                    st.markdown(f"> Current f-number = {f_number:.1f}, focal length = {focal_length:.0f} mm")

                # 8. Recommendations
                bestN = min(cand, key=lambda x: x[0])
                bestF = min(cand, key=lambda x: x[1])
                st.markdown("----")
                st.markdown(f"**Recommendation1 (min Δf-number):** f-number = {bestN[2]:.1f}, focal length = {bestN[3]:.0f} mm")
                st.markdown(f"**Recommendation2 (min Δfocal length):** focal length = {bestF[3]:.0f} mm, f-number = {bestF[2]:.1f}")



