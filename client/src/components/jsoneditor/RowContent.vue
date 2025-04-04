<script setup>
import AnswerSpaceContent from './AnswerSpaceContent.vue';
import DiagramContent from './DiagramContent.vue';
import TextContent from './TextContent.vue';

const props = defineProps({
  content: {
    type: Array,
    required: true
  },
})
</script>

<template>
  <div class="flex grid items-center gap-4" :class="`grid-cols-${props.content.length}`">
    <div v-for="item in props.content">
      <div v-if="item.type === 'text'">
        <TextContent :content="item" />
      </div>
      <div v-if="item.type === 'diagram'">
        <DiagramContent :content="item" />
      </div>
      <div v-if="item.type === 'answer_space'">
        <AnswerSpaceContent :content="item" />
      </div>
    </div>
  </div>
</template>