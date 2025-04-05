import streamlit as st

st.title("Restaurant Selection")
st.subheader("Find the best restaurant for Phong!")
st.subheader("Free Ads: Green Basil Dimsum & Pho")

with st.sidebar:
    distant = st.slider("Distance", 0, 100) * 1000  # 0 to 100 km
    price = st.slider("Price", 0, 4)  # 0 to 4
    restaurant_type = st.selectbox("Restaurant Type", [
        "All", "Japanese", "Chinese", "Italian", "French", "Indian", "Mexican", "American", "Thai", "Spanish", "Greek", "Turkish", "Vietnamese", "Korean",
        "Mediterranean", "African", "Caribbean", "British", "Russian", "Brazilian", "Argentinian", "Peruvian", "Colombian", "Chilean", "Cuban", "Jamaican", "Haitian"
    ])

like = st.button("Like")
dislike = st.button("Dislike")