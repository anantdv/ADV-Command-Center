import type { TrainingLesson } from '../../types/training'
export function LessonViewer({lesson}:{lesson?:TrainingLesson}){return <section className="card p-5"><h3 className="font-bold">{lesson?.title||'Select a lesson'}</h3><p className="mt-3 text-sm leading-6 text-slate-600">{lesson?.content||'Course lessons appear here with private role-based access.'}</p></section>}
