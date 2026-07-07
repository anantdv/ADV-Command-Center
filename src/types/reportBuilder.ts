export type ReportColumn={key:string;label:string;fieldtype:string;visible:boolean;source:'doctype'|'report'|'computed'}
export type ReportRunWithColumnsRequest={source_type:'doctype'|'report';source_name:string;filters?:Record<string,unknown>;columns?:string[];limit?:number;order_by?:string|null}
export type ReportRunWithColumnsResponse={source_type:string;source_name:string;columns:ReportColumn[];rows:Array<Record<string,unknown>>;total_rows:number;permission?:Record<string,unknown>|null}
export type ReportDiagnosticResponse={report_name:string;allowed_by_backend:boolean;allowed_by_frappe:boolean|null;method_path:string;filters_used:Record<string,unknown>;frappe_response_shape:Record<string,unknown>;errors:string[];recommendations:string[]}
