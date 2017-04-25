from invoice_parser import estimate_invoice_name
if __name__=='__main__':
    input_dir= './input/*.pdf'
    output_dir= './predicted_output/'
    estimate_invoice_name(input_dir,output_dir)




