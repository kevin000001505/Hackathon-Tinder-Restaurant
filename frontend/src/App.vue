<!-- src/views/AppPage.vue -->
<template>
    <Drawer v-model:visible="drawer" header="Settings">
        <Card>
            <template #title>Distance {{ distance }}</template>
            <template #content>
                <Slider v-model="distance" min="5" max="50"/>
            </template>
        </Card>
    </Drawer>
    <div class="flex w-dvw h-dvh justify-center">
        <div class="flex flex-col w-7/10 h-full">
            <div class="flex h-1/80 py-0.5">
                <ProgressBar :value="progress0" style="--p-progressbar-height: 100%" class="w-1/3 no-transition-bar" :showValue="false"/>
                <ProgressBar :value="progress1" style="--p-progressbar-height: 100%" class="w-1/3 no-transition-bar" :showValue="false"/>
                <ProgressBar :value="progress2" style="--p-progressbar-height: 100%" class="w-1/3 no-transition-bar" :showValue="false"/>
            </div>
            <div class="flex justify-center h-6/10 lg:h-7/10 pb-3">
                <ProgressSpinner v-if="loading" class="h-full w-full"/>
                <img v-else :src="image" class="h-full w-full object-cover rounded-xl"/>
            </div>
            <div class="h-3/10 lg:h-1/5 pb-3">
                <ScrollPanel style="width: 100%; height: 100%">
                    <Skeleton v-if="loading" class="mb-2"></Skeleton>
                    <Skeleton v-if="loading" width="10rem" class="mb-2"></Skeleton>
                    <Skeleton v-if="loading" width="5rem" class="mb-2"></Skeleton>
                    <Skeleton v-if="loading" height="2rem" class="mb-2"></Skeleton>
                    <Skeleton v-if="loading" width="10rem" height="4rem"></Skeleton>
                    <div v-else>
                        <h1><span class="material-icons">storefront</span>{{ r_name }}</h1>
                        <p><span class="material-icons">location_on</span>{{ r_addr }}</p>
                        <p><span class="material-icons">attach_money</span>{{ r_price }} | <span class="material-icons">star</span>{{ r_rating }}</p>
                        <p><span class="material-icons">call</span>{{ r_phone }}</p>
                        <p>{{ r_summary }}</p>
                        <p><span class="material-icons">local_convenience_store</span></p>
                        <p>{{ r_hours[0] }}</p>
                        <p>{{ r_hours[1] }}</p>
                        <p>{{ r_hours[2] }}</p>
                        <p>{{ r_hours[3] }}</p>
                        <p>{{ r_hours[4] }}</p>
                        <p>{{ r_hours[5] }}</p>
                        <p>{{ r_hours[6] }}</p>
                    </div>
                </ScrollPanel>
            </div>
            <div class="flex justify-center max-h-1/10">
                <div class="flex gap-x-[5vw]">
                    <Button raised rounded @click="drawer = true"><span class="material-icons">menu</span></Button>
                    <Button raised rounded @click="dislike"><span class="material-icons">close</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">search</span></Button>
                    <Button raised rounded @click="like"><span class="material-icons">favorite</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">info</span></Button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import Drawer from 'primevue/drawer';
import Button from 'primevue/button';
import Slider from 'primevue/slider';
import Card from 'primevue/card';
import ScrollPanel from 'primevue/scrollpanel';
import ProgressBar from 'primevue/progressbar';
import ProgressSpinner from 'primevue/progressspinner';
import Skeleton from 'primevue/skeleton';
import { ref, computed, onMounted } from "vue";
import { userId } from '@/router/index.js';

const latitude = ref(38.85283523403844);
const longitude = ref(-77.33180841736046);
const locationError = ref('');

const getLocation = () => {
  locationError.value = '';
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        latitude.value = position.coords.latitude;
        longitude.value = position.coords.longitude;
        console.log('Latitude:', latitude.value, 'Longitude:', longitude.value);
      },
      (error) => {
        handleLocationError(error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  }
};

const handleLocationError = (error) => {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        locationError.value = 'User denied the request for Geolocation.';
        break;
      case error.POSITION_UNAVAILABLE:
        locationError.value = 'Location information is unavailable.';
        break;
      case error.TIMEOUT:
        locationError.value = 'The request to get user location timed out.';
        break;
      default:
        locationError.value = 'An unknown error occurred.';
    }
}

const likes = ref([]);
const dislikes = ref([]);
const restaurant_index = ref(0);
const restaurants_info = ref();
const r_name = ref();
const r_addr = ref();
const r_price = ref();
const r_rating = ref();
const r_phone = ref();
const r_summary = ref();
const r_hours = ref();
const backend_url = 'http://127.0.0.1:5000/'
async function getRestaurantsInfo() {
    loading.value = true;
    getLocation();
    const response = await fetch(`${backend_url}search?lat=${latitude.value}&lng=${longitude.value}&radius=${distance.value * 1000}?user_id=${userId.value}`, {
        method: 'GET',
        credentials: 'include',
    });
    let restaurants = await response.json();
    restaurants_info.value = restaurants.results;
    displayRestaurantInfo();
}

function displayRestaurantInfo() {
    if (!restaurants_info.value || restaurant_index.value >= restaurants_info.value.length) {
        console.error('No more restaurants to display or restaurant data is undefined');
        return;
    }
    
    r_name.value = restaurants_info.value[restaurant_index.value].restaurant_name;
    r_addr.value = restaurants_info.value[restaurant_index.value].formatted_address;
    r_price.value = restaurants_info.value[restaurant_index.value].price_level;
    r_rating.value = restaurants_info.value[restaurant_index.value].rating;
    r_phone.value = restaurants_info.value[restaurant_index.value].phone_number;
    r_summary.value = restaurants_info.value[restaurant_index.value].editorial_summary;
    r_hours.value = restaurants_info.value[restaurant_index.value].opening_hours;
    getRestaurantPhotos(restaurants_info.value[restaurant_index.value].place_id);
}

const interact_counter = ref(0);

async function send_preferences() {
    if (interact_counter.value % 5 == 0) {
        loading.value = true;
        const response = await fetch(`${backend_url}suggestion`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId.value,
                like_place_id: likes.value,
                dislike_place_id: dislikes.value,
            }),
        });
        
        const data = await response.json();
        console.log('Suggestion response:', data);
        
        // Fix: The API returns data.suggestion instead of data.results
        if (data && data.suggestion && data.suggestion.length > 0) {
            // Update restaurant list with the suggested restaurants
            restaurants_info.value = data.suggestion;
            // Reset the restaurant index to start showing the first suggested restaurant
            restaurant_index.value = 0;
            // Clear previous likes and dislikes after they've been processed
            likes.value = [];
            dislikes.value = [];
            // Display the first suggested restaurant
            displayRestaurantInfo();
        } else {
            console.log('No suggestions received or empty response');
            // If no suggestions, let's get new restaurants
            await getRestaurantsInfo();
        }
    }
}

async function like() {
    interact_counter.value++;
    likes.value.push(placeID.value);
    
    await send_preferences();
    
    // Only increment and display if we didn't reset the index in send_preferences
    if (restaurant_index.value + 1 < restaurants_info.value.length) {
        restaurant_index.value++;
        displayRestaurantInfo();
    } else if (restaurant_index.value + 1 >= restaurants_info.value.length) {
        // We're at the end of our list, get more restaurants
        await getRestaurantsInfo();
    }
}

async function dislike() {
    interact_counter.value++;
    dislikes.value.push(placeID.value);
    
    await send_preferences();
    
    // Only increment and display if we didn't reset the index in send_preferences
    if (restaurant_index.value + 1 < restaurants_info.value.length) {
        restaurant_index.value++;
        displayRestaurantInfo();
    } else if (restaurant_index.value + 1 >= restaurants_info.value.length) {
        // We're at the end of our list, get more restaurants
        await getRestaurantsInfo();
    }
}

const loading = ref(true);
const progress0 = ref(0);
const progress1 = ref(0);
const progress2 = ref(0);
const stepCounter = ref(0);
const placeID = ref()
const image = ref(null);
const imageID = ref();
const photoTnterval = ref(null);
const duration = 5000; // total time from 0 to 100 in ms
const intervalRate = 25; // ms between updates
const numSteps = duration / intervalRate;
const step = 100 / numSteps;

// Loop between restaurant photos every 5 seconds
function setPhoto() {
    switch (imageID.value) {
        case 0:
            progress0.value = Math.min(progress0.value + step, 100);
            break;
        case 1:
            progress1.value = Math.min(progress1.value + step, 100);
            break;
        case 2:
            progress2.value = Math.min(progress2.value + step, 100);
            break;
    }
    stepCounter.value = (stepCounter.value + 1) % numSteps;
    if (stepCounter.value == 0) {
        if (imageID.value == 2) {
            progress0.value = 0;
            progress1.value = 0;
            progress2.value = 0;
        }
        imageID.value = (imageID.value + 1) % 3;
        image.value = images[imageID.value].src;
    }
}

function startGallery() {
    loading.value = false;
    clearInterval(photoTnterval.value);
    image.value = images[imageID.value].src;
    photoTnterval.value = setInterval(setPhoto, intervalRate);
}

var imageURLs = [];
var images = [];

async function getRestaurantPhotos(place_id) {
    try {
        images = [];
        placeID.value = place_id;
        imageID.value = 0;
        stepCounter.value = 0;
        progress0.value = 0;
        progress1.value = 0;
        progress2.value = 0;
        imageURLs = [
            backend_url + 'photos/' + placeID.value + '/0',
            backend_url + 'photos/' + placeID.value + '/1',
            backend_url + 'photos/' + placeID.value + '/2'
        ]

        let loadedImagesCount = 0;
        for (let i = 0; i < imageURLs.length; i++) {
            const img = new Image();
            img.src = imageURLs[i];

            img.onload = () => {
                loadedImagesCount++;
                if (loadedImagesCount === imageURLs.length) {
                    startGallery();
                }
            };

            img.onerror = () => {
                loadedImagesCount++;
                console.error(`Error loading image: ${imageURLs[i]}`);
                if (loadedImagesCount === imageURLs.length) {
                    startGallery();
                }
            };
            images.push(img);
        }
    } catch (error) {
        console.error('Error fetching images:', error);
    }
}

onMounted(() => {
    getRestaurantsInfo()
})

const drawer = ref(false);
const distance = ref(15);
</script>

<style>
.no-transition-bar .p-progressbar-value {
  transition: none !important;
}
</style>