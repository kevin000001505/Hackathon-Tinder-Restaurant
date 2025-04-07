import streamlit as st
from google_map_search import GoogleMapSearch

gmaps = GoogleMapSearch()

restaurant_types = [
    "All", "Japanese", "Chinese", "Italian", "French", "Indian", "Mexican", "American", "Thai", "Spanish", "Greek", "Turkish", "Vietnamese", "Korean",
    "Mediterranean", "African", "Caribbean", "British", "Russian", "Brazilian", "Argentinian", "Peruvian", "Colombian", "Chilean", "Cuban", "Jamaican", "Haitian"
]

st.title("Restaurant Selection")
st.subheader("Find the best restaurant for Phong!")
st.subheader("Free Ads: Green Basil Dimsum & Pho")

with st.sidebar:
    distant = st.slider("Distance", 0, 100) * 1000  # 0 to 100 km
    price = st.slider("Price", 0, 4)  # 0 to 4
    restaurant_type = st.selectbox("Restaurant Type", restaurant_types)

location_button = st.button("Get your location")
if location_button:
    location = gmaps.get_self_geocode()

# address = st.text_input("Please enter your address")
# if address:
#     location = gmaps.search_place(address)
#     st.write(f"Location: {location}")

# like = st.button("Like")
# dislike = st.button("Dislike")
img_data = [
    "photo.jpg",
    "photo2.jpg",
    "photo1.jpg",
]

# Initialize session state variables
if "img_index" not in st.session_state:
    st.session_state.img_index = 0

if "liked_images" not in st.session_state:
    st.session_state.liked_images = []

def show_next_image():
    """Advance to the next image; wrap around if at end."""
    if st.session_state.img_index < len(img_data) - 1:
        st.session_state.img_index += 1
    else:
        st.session_state.img_index = 0

st.title("Interactive Image Selector")

# Sidebar: Show Cart
with st.sidebar:
    if st.button("Show Cart"):
        st.subheader("Liked Images")
        if st.session_state.liked_images:
            for img in st.session_state.liked_images:
                st.image(img)
        else:
            st.write("No liked images yet.")

# Display the current image
current_image = img_data[st.session_state.img_index]
st.image(current_image, caption=f"Image {st.session_state.img_index + 1}")

# Two buttons for Like and Dislike
col1, col2 = st.columns(2)
with col1:
    if st.button("Like"):
        # Add current image to liked images if not already added
        if current_image not in st.session_state.liked_images:
            st.session_state.liked_images.append(current_image)
        show_next_image()
with col2:
    if st.button("Dislike"):
        show_next_image()