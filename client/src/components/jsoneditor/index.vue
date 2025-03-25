<script setup>
import ContentFlow from './ContentFlow.vue';
import MainQuestionContentFlow from './MainQuestionContentFlow.vue';
import MarksDisplay from './MarksDisplay.vue';

defineProps({
  sections: {
    type: Array,
    required: false
  }
});

// const validContentTypes = (content) => {
//   if (content.type === 'text') {
//     // Check if the content has both 'malay' and 'english' properties
//     return content.text && content.text.malay && content.text.english;
//   }
//   return content.type === 'diagram' || content.type === 'answer_space';
// };

</script>

<template>
  <div class="p-6 space-y-4 text-black">
    <div v-for="section in sections">
      <div class="space-y-8 mt-4">
        <template v-for="mainQuestion in section.main_questions" :key="mainQuestion.number">
          <div class="border p-4 rounded-md bg-white shadow-md text-left">
            <table class="w-full border-collapse border mt-2 bg-gray-50" style="table-layout: auto;">
              <tbody>

                <!-- main questions -->
                <template v-for="(content, index) in mainQuestion.content_flow" :key="content.number">
                  <MainQuestionContentFlow :content="content" :index="index" :number="mainQuestion.number" />
                </template>

                <!-- questions -->
                <template v-for="question in mainQuestion.questions" :key="question.number">
                  <template v-for="(content, index) in question.content_flow" :key="content.number">
                    <tr v-if="content.type != 'sub_questions'" class="border bg-gray-100">
                      <td class="w-auto"></td>
                      <td v-if="question.number && index === 0" class="border p-2 w-auto">
                        {{ question.number.replace(/^\d+/, "") }}
                      </td>
                      <td v-else class="border p-2 w-auto"></td>
                      <td class="border p-2 space-y-6 w-full" colspan="2">
                        <ContentFlow :content="content" />
                      </td>
                    </tr>
                  </template>

                  <tr v-if="question.marks" class="border bg-gray-100">
                    <td></td>
                    <td></td>
                    <td colspan="2" align="right">
                      <MarksDisplay :marks="question.marks" />
                    </td>
                  </tr>

                  <!-- sub questions -->
                  <template v-for="subQuestion in question.sub_questions" :key="subQuestion.number">
                    <template v-for="(content, index) in subQuestion.content_flow" :key="content.number">
                      <tr class="border">
                        <td class="w-auto"></td>
                        <td class="w-auto"></td>
                        <td v-if="question.number && index === 0" class="p-2 w-auto">
                          {{ subQuestion.number.match(/\([^)]*\)$/)?.[0] }}
                        </td>
                        <td v-else></td>
                        <td class="p-2 space-y-6 w-full">
                          <ContentFlow :content="content" />
                        </td>
                      </tr>
                    </template>

                    <tr v-if="subQuestion.marks" class="border bg-gray-100" align="right">
                      <td></td>
                      <td></td>
                      <td></td>
                      <td colspan="2">
                        <MarksDisplay :marks="subQuestion.marks" />
                      </td>
                    </tr>
                  </template>

                </template>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
th,
td {
  border: 1px solid black;
  padding: 8px;
  vertical-align: top;
}
</style>
