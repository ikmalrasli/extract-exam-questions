<script setup>
import { computed

 } from 'vue';
const props = defineProps({
  content: {
    type: Object,
    required: true
  },
})

const formattedMalay = computed(() => {
  const text = props.content.text.malay.replace(/\\n/g, '<br />'); 
  return text;
})

const formattedEnglish = computed(() => {
  const text = props.content.text.english.replace(/\\n/g, '<br />');
  return text;
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <div v-html="formattedMalay"></div>
    <div class="italic" v-html="formattedEnglish"></div>
  </div>
</template>