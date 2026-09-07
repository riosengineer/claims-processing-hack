#!/usr/bin/env python3
"""
Claims Processing UI
Streamlit frontend for the Claims Processing REST API
"""
import os
import json
import base64
import httpx
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/workspaces/claims-processing-hack/.env")

# Page configuration
st.set_page_config(
    page_title="Claims Processing System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; margin-bottom: 1rem; }
    .status-success { background-color: #D1FAE5; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #10B981; }
    .status-error { background-color: #FEE2E2; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #EF4444; }
</style>
""", unsafe_allow_html=True)

# Default API URL - Container Apps direct URL
DEFAULT_API_URL = "https://claims-processing-api.gentletree-b8a57f24.swedencentral.azurecontainerapps.io"


def get_api_url():
    if "api_url" not in st.session_state:
        st.session_state.api_url = os.environ.get("API_URL", DEFAULT_API_URL)
    return st.session_state.api_url


def check_health(api_url: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_url}/health")
            return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def process_claim(api_url: str, file_content: bytes, filename: str) -> dict:
    try:
        with httpx.Client(timeout=120.0) as client:
            files = {"file": (filename, file_content, "image/jpeg")}
            response = client.post(f"{api_url}/process-claim/upload", files=files)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def display_results(data: dict):
    if not data:
        return
    
    # Vehicle Information
    if "vehicle_info" in data:
        st.subheader("🚗 Vehicle Information")
        v = data["vehicle_info"]
        cols = st.columns(4)
        cols[0].metric("Make", v.get("make", "N/A"))
        cols[1].metric("Model", v.get("model", "N/A"))
        cols[2].metric("Color", v.get("color", "N/A"))
        cols[3].metric("Year", v.get("year", "N/A"))
    
    # Damage Assessment
    if "damage_assessment" in data:
        st.subheader("💥 Damage Assessment")
        d = data["damage_assessment"]
        cols = st.columns(3)
        severity = d.get("severity", "N/A")
        icon = {"minor": "🟢", "moderate": "🟡", "severe": "🔴"}.get(str(severity).lower(), "⚪")
        cols[0].metric("Severity", f"{icon} {severity}")
        cost = d.get("estimated_cost", "N/A")
        cols[1].metric("Estimated Cost", f"${cost:,.2f}" if isinstance(cost, (int, float)) else cost)
        areas = d.get("affected_areas", [])
        cols[2].metric("Affected Areas", len(areas) if isinstance(areas, list) else "N/A")
        if areas:
            st.markdown("**Areas:** " + ", ".join(areas))
    
    # Incident Information
    if "incident_info" in data:
        st.subheader("📋 Incident Information")
        i = data["incident_info"]
        st.markdown(f"**Date:** {i.get('date', 'N/A')} | **Location:** {i.get('location', 'N/A')}")
        st.markdown(f"**Description:** {i.get('description', 'N/A')}")

    coverage = data.get("coverage_validation")
    if coverage:
        st.subheader("🛡️ Coverage Validation")

        policy = coverage.get("policy_match", {})
        determination = coverage.get("coverage_determination", {})
        decision = determination.get("decision", "UNKNOWN")
        policy_name = policy.get("policy_name", "N/A")

        if decision == "APPROVED":
            st.success(f"Coverage approved — {policy_name}")
        elif decision == "DENIED":
            st.error(f"Coverage denied — {policy_name}")
        elif decision == "PARTIAL_COVERAGE":
            st.warning(f"Partial coverage — {policy_name}")
        else:
            st.info(f"Coverage decision: {decision} — {policy_name}")

        cols = st.columns(3)
        cols[0].metric("Decision", decision)
        cols[1].metric("Deductible", determination.get("deductible", "N/A"))
        cols[2].metric("Coverage Limit", determination.get("coverage_limit", "N/A"))

        applicable = determination.get("applicable_coverage")
        if applicable:
            st.markdown(f"**Applicable coverage:** {applicable}")

        reasoning = determination.get("reasoning")
        if reasoning:
            st.markdown(f"**Reasoning:** {reasoning}")

        exclusions = determination.get("exclusions_triggered", [])
        if exclusions:
            st.markdown("**Exclusions triggered:** " + "; ".join(str(item) for item in exclusions))

        recommendations = determination.get("recommendations")
        if recommendations:
            st.markdown(f"**Recommendations:** {recommendations}")


def main():
    st.markdown('<p class="main-header">🚗 Insurance Claims Processing</p>', unsafe_allow_html=True)
    st.markdown("Upload claim images to extract structured data using AI")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_url = st.text_input("API URL", value=get_api_url())
        st.session_state.api_url = api_url
        
        if st.button("🏥 Check Health", use_container_width=True):
            with st.spinner("Checking..."):
                result = check_health(api_url)
                if result.get("status") == "healthy":
                    st.success(f"✅ API Healthy\n\n{result.get('service', '')}")
                else:
                    st.error(f"❌ {result.get('error', 'Error')}")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📤 Upload Claim")
        uploaded = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
        process_btn = st.button("🚀 Process Claim", type="primary", use_container_width=True, disabled=not uploaded)
    
    with col2:
        if uploaded:
            st.image(uploaded, caption=uploaded.name, width=200)
    
    # Process
    if process_btn and uploaded:
        st.divider()
        with st.spinner("🔄 Processing and validating coverage... (30-60 seconds)"):
            result = process_claim(st.session_state.api_url, uploaded.getvalue(), uploaded.name)
        
        st.header("📋 Results")
        if result.get("success"):
            st.markdown('<div class="status-success">✅ Claim processed successfully!</div>', unsafe_allow_html=True)
            display_results(result.get("data", {}))
            with st.expander("🔍 Raw JSON"):
                st.json(result)
        else:
            st.markdown(f'<div class="status-error">❌ Error: {result.get("error", "Unknown")}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
