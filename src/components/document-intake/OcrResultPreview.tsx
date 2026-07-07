import type { OCRResult } from '../../types/documentIntake'

export function OcrResultPreview({ocr}:{ocr:OCRResult}){
 return <div className="rounded-2xl border border-slate-200 bg-white p-4"><h3 className="text-sm font-bold text-slate-900">OCR Preview</h3><p className="mt-1 text-xs text-slate-400">Pages: {ocr.page_count??'—'}</p><pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-4 text-xs text-slate-100">{ocr.extracted_text_preview||'No text extracted.'}</pre></div>
}
