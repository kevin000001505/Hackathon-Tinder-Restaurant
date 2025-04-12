<template>
    <Toast />
    <ConfirmDialog></ConfirmDialog>
    <Drawer v-model:visible="drawer" header="Settings">
        <Card>
            <template #title>Distance {{ distance }}</template>
            <template #content>
                <Slider v-model="distance" min="5" max="50"/>
            </template>
        </Card>
        <Card>
            <template #title>Price {{ priceDisplay }}</template>
            <template #content>
                <Slider v-model="price" :min="1" :max="4" :step="1"/>
            </template>
        </Card>
        <Card>
            <template #title>🍙 Subscribe to Restaurant Tinder Plus Premium to remove ads 🍙</template>
            <template #content>
                <div class="flex flex-col justify-center">
                    <Button label="Only $49.99/year" @click="adButton()"></Button>
                    Less than your Netflix subscription!
                </div>
            </template>
        </Card>
    </Drawer>
    <div class="flex w-dvw h-dvh justify-center">
        <div v-if="!isMobile" class="absolute flex justify-center top-0 left-0 w-3/20 h-full">
            <img src="./assets/attach_money.svg"></img>
        </div>
        <div :class="isMobile ? 'flex flex-col h-full w-17/20' : 'flex flex-col h-full w-7/10'">
            <div class="flex h-1/80 py-0.5">
                <ProgressBar :value="progress0" style="--p-progressbar-height: 100%" class="w-1/3" :showValue="false"/>
                <ProgressBar :value="progress1" style="--p-progressbar-height: 100%" class="w-1/3" :showValue="false"/>
                <ProgressBar :value="progress2" style="--p-progressbar-height: 100%" class="w-1/3" :showValue="false"/>
            </div>
            <div class="flex justify-center h-6/10 lg:h-7/10 pb-3">
                <img :src=image class="h-full w-full object-cover rounded-xl"/>
            </div>
            <div class="h-3/10 lg:h-1/5 pb-3">
                <ScrollPanel style="width: 100%; height: 100%">
                    <p>
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                    </p>
                    <p>
                        Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam
                        voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Consectetur, adipisci velit, sed quia non numquam eius modi.
                    </p>
                    <p>
                        At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui
                        officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus.
                    </p>
                    <p class="m-0">
                        Quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non
                        recusandae. Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat
                    </p>
                </ScrollPanel>
            </div>
            <div class="flex justify-center max-h-1/10">
                <div class="flex gap-x-[5vw]">
                    <Button raised rounded @click="drawer = true"><span class="material-icons">menu</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">close</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">search</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">favorite</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">info</span></Button>
                </div>
            </div>
        </div>
        <div v-if="!isMobile" class="absolute flex justify-center top-0 right-0 w-3/20 h-full">
            <img src="./assets/attach_money.svg">
        </img></div>
    </div>
</template>

<script setup>
import Drawer from 'primevue/drawer';
import Button from 'primevue/button';
import Slider from 'primevue/slider';
import Card from 'primevue/card';
import ScrollPanel from 'primevue/scrollpanel';
import ProgressBar from 'primevue/progressbar';
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import ConfirmDialog from 'primevue/confirmdialog';
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import Toast from 'primevue/toast';

const confirm = useConfirm();
const toast = useToast();

const adButton = () => {
    confirm.require({
        message: 'We haven\'t implement our payment system yet...',
        header: '😔 Sorry 😔',
        icon: 'pi pi-exclamation-triangle',
        acceptProps: {
            label: 'Ok 😒'
        },
        rejectProps: {
            label: 'Cancel',
            severity: 'danger',
            outlined: true
        },
        accept: () => {
            toast.add({ severity: 'info', summary: 'Confirmed', detail: 'We are open to the idea though 🤑', life: 3000 });
        },
        reject: () => {
            toast.add({ severity: 'error', summary: 'Cancel', detail: 'Give it some though? 😦', life: 3000 });
        }
    });
};

const restaurant_info = ref();
const backend_url = 'http://127.0.0.1:5000'
async function getRestaurantsInfo() {
    const response = await fetch(backend_url + '/search?' + new URLSearchParams({
        lat: 38.85283523403844,
        lng: -77.33180841736046,
    }).toString());
    restaurant_info.value = await response.json();
    console.log(restaurant_info.value.results);
    getRestaurantPhotos(restaurant_info.value.results[0].place_id)
}

const progress0 = ref(0);
const progress1 = ref(0);
const progress2 = ref(0);
const stepCounter = ref(0);
const placeID = ref()
const image = ref();
const imageID = ref();
const photoTnterval = ref();

// Loop between restaurant photos every 5 seconds
function setPhoto() {
    switch (imageID.value) {
        case 0:
            progress0.value = Math.min(progress0.value + 2, 100);
            break;
        case 1:
            progress1.value = Math.min(progress1.value + 2, 100);
            break;
        case 2:
            progress2.value = Math.min(progress2.value + 2, 100);
            break;
    }
    stepCounter.value = (stepCounter.value + 1) % 50;
    if (stepCounter.value == 0) {
        if (imageID.value == 2) {
            progress0.value = 0;
            progress1.value = 0;
            progress2.value = 0;
        }
        image.value = backend_url + '/photos/' + placeID.value + '/' + imageID.value;
        imageID.value = (imageID.value + 1) % 3;
    }
}

async function getRestaurantPhotos(place_id) {
    try {
        placeID.value = place_id;
        imageID.value = 0;
        stepCounter.value = 0;
        clearInterval(photoTnterval.value);
        photoTnterval.value = setInterval(setPhoto, 100);
    } catch (error) {
        console.error('Error fetching images:', error);
    }
}

const isMobile = ref(checkIsMobile());
function checkIsMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i
    .test(navigator.userAgent)
}

function updateIsMobile() {
  isMobile.value = checkIsMobile();
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateIsMobile);
});

onMounted(() => {
    window.addEventListener('resize', updateIsMobile);
    getRestaurantsInfo();
})

const drawer = ref(false);
const distance = ref(15);
const price = ref(2);
const priceDisplay = computed(() => '$'.repeat(price.value));
</script>
