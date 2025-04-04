<script setup>
import AnswerSpaceContent from './AnswerSpaceContent.vue';
import DiagramContent from './DiagramContent.vue';
import TableContent from './TableContent.vue';
import TextContent from './TextContent.vue';
import RowContent from './RowContent.vue';

const props = defineProps({
  content: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <div v-if="content.type === 'text'">
    <TextContent :content="content" />
  </div>
  <div v-if="content.type === 'diagram'">
    <DiagramContent :content="content" />
  </div>
  <div v-if="content.type === 'table'">
    <TableContent :content="content" />
  </div>
  <div v-if="content.type === 'answer_space'">
    <AnswerSpaceContent :content="content" />
  </div>
  <div v-if="content.type === 'row'">
    <RowContent :content="content.items" />
  </div>
</template>