/**
 * Campaign form types
 */

export type QuestionId = "style" | "audience" | "emotion" | "pacing" | "colors"

export interface Question {
  id: QuestionId
  question: string
  options: readonly string[]
}

export interface CampaignAnswers {
  style?: string
  audience?: string
  emotion?: string
  pacing?: string
  colors?: string
  ideas?: string
}

export interface SubmitCampaignAnswersResponse {
  creative_bible_id: string
  message: string
}

export interface CampaignPreferences extends Record<string, string> {
  style: string
  audience: string
  emotion: string
  pacing: string
  colors: string
  ideas: string
}
