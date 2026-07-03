export type KnowledgeSourceType='training_course'|'training_lesson'|'training_assessment'|'support_article'|'sop_document'|'faq'|'uploaded_document'|'media_transcript'
export type KnowledgeSource={sourceId:string;title:string;sourceType:KnowledgeSourceType;module?:string|null;description?:string|null;status:'draft'|'approved'|'archived';allowedRoles:string[];allowedModules:string[];createdBy?:string|null;createdAt:string;updatedAt?:string|null}
export type KnowledgeSourceCreate={title:string;sourceType:KnowledgeSourceType;module?:string;description?:string;content?:string;fileId?:string;allowedRoles?:string[];allowedModules?:string[]}
export type KnowledgeSearchResult={chunkId:string;sourceId:string;title:string;snippet:string;score:number;citationLabel:string;sourceType:KnowledgeSourceType;module?:string|null}
export type RAGCitation={citationId:string;sourceId:string;title:string;citationLabel:string;snippet:string;sourceType?:KnowledgeSourceType|null}
export type RAGAnswer={answer:string;citations:RAGCitation[];confidence?:number|null;escalationRecommended:boolean;escalationReason?:string|null}
export type RAGAnswerRequest={question:string;module?:string;conversationId?:string;topK?:number}
