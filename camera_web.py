import streamlit as st
import math
import matplotlib.pyplot as plt

st.title("📷 Face Recognition Calculator with Visual Indicator")

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

            # 簡化版電池條狀圖
            st.write("### Visual Indicator (Face Pixel Occupancy)")

            fig, ax = plt.subplots(figsize=(6, 1.5))
            max_px = 80.0
            fill_px = min(px_for_18cm, max_px)
            fill_ratio = fill_px / max_px * 100

            ax.barh(0, fill_px, color="green")
            ax.barh(0, max_px - fill_px, left=fill_px, color="lightgray")
            ax.set_xlim(0, max_px)
            ax.set_yticks([])
            ax.set_xticks([])
            ax.set_title(f"Face Pixel Occupancy: {fill_px:.1f} px / 80 px ({fill_ratio:.1f}%)")

            st.pyplot(fig)
