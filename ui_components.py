

import streamlit as st
import uuid

def odds_input(label, default=None):
    unique_key = f"odds_{label}_{uuid.uuid4().hex[:6]}"
    return st.number_input(
        label,
        min_value=1.01,
        step=0.01,
        value=float(default or 1.0),
        key=unique_key
    )
