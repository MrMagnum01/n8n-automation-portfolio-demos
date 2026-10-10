// One row per problem found -> exceptions.csv (file, invoice_no, reason, detail)
return $input.all().flatMap(({ json: i }) => i.issues.map(x => ({ json: {
  file: i.file, invoice_no: i.invoice_no ?? '', reason: x.code, detail: x.detail,
} })));
