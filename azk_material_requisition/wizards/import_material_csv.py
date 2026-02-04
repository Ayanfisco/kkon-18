from odoo import models, fields, api, _
import os
import csv
import base64
import logging
from odoo.tools.config import config
from odoo.exceptions import ValidationError

log = logging.getLogger(__name__)

class ImportMaterilaCsv(models.TransientModel):
    _name = 'az.import.materila.csv'
    _description = 'Import material csv file'
    
    mr_id = fields.Many2many('material.requisition', string='Material requisition')
    csv_file = fields.Many2many('ir.attachment', string='CSV File', required="1")
    file_lines_count = fields.Integer('File Lines Count', readonly=True)
    created_lines_count = fields.Integer('Imported Lines count', readonly=True)
    updated_lines_count = fields.Integer('Updated Lines Count', readonly=True)
    not_found_lines_count = fields.Integer('Not Found product Count', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if len(rec.csv_file) > 1:
                raise ValidationError(_('Only one file is allowed'))
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if len(rec.csv_file) > 1:
                raise ValidationError(_('Only one file is allowed'))
        
        return res
    
    def import_csv_file(self):
        if not self.csv_file:
            raise ValidationError(_('Please Upload a CSV file.'))
        
        source_path = self.csv_file._full_path(self.csv_file.store_fname)
        file_open = open(source_path,'rt', encoding='utf-8-sig')
        reader = csv.DictReader(file_open, delimiter=',')
        
        to_create = []
        to_update = []
        not_found = []
        lines_count = 0
        log.info("Start importing file: %s for MR: %s", self.csv_file.name, self.mr_id.name)
        
        #check header
        file_header = ['Product Code', 'Description', 'Quantity', 'Product UOM']
        for header in file_header:
            if header not in reader.fieldnames:
                raise ValidationError(_('Uploaded File must have the following headers: %s') % (file_header))
            
        for line, row in enumerate(reader, start=2):
            product_code = row['Product Code']
            if not product_code:
                raise ValidationError(_('Missing product code at line %s') % (line))
            
            found_product = self.env['product.template'].search([('default_code', '=', product_code.strip())])
            if found_product:
                uom = row['Product UOM']
                found_uom = False
                if uom:
                    found_uom = self.env['uom.uom'].search([('name', '=', uom.strip())])
                    if not found_uom:
                        raise ValidationError(_('Product UOM was not found at line %s') % (line))
                    else:
                        found_uom = found_uom[0]
                        if len(found_product) > 1:
                            product_with_same_uom = found_product.filtered(lambda p: p.uom_id.id == found_uom.id or p.uom_id.category_id.id == found_uom.category_id.id)
                            if product_with_same_uom:
                                found_product = product_with_same_uom
                        
                        found_product = found_product[0]
                        if found_product.uom_id.category_id.id != found_uom.category_id.id:
                            raise ValidationError(_('Product UOM at line %s is not valid,must be category: %s') % (line, found_product.uom_id.category_id.name))
                    
                found_mr_line = self.mr_id.line_ids.filtered(lambda l: l.product_template_id.id == found_product.id)
                if found_mr_line:
                    to_update.append({'id': found_mr_line.id,
                                     'requested_qty': row['Quantity']
                                    })
                else:
                    to_create.append({'product_template_id': found_product.id,
                                      'requested_qty': row['Quantity'],
                                      'description': row['Description'],
                                      'requisition_id': self.mr_id.id,
                                      'product_uom_id': found_uom.id if found_uom else False,
                                    })
            else:
                not_found.append(row)
                
            lines_count += 1
        
        if to_create:
            self.env['material.requisition.line'].create(to_create)
        if to_update:
            for line in to_update:
                self.env['material.requisition.line'].browse(line['id']).update({'requested_qty': line['requested_qty']})
        
        self.file_lines_count = lines_count
        self.created_lines_count = len(to_create)
        self.updated_lines_count = len(to_update)
        self.not_found_lines_count = len(not_found)
        
        log.info("Finish importing file %s for Mr %s : %s lines created,%s lines updated, %s lines not found.", self.csv_file.name, self.mr_id.name, len(to_create), len(to_update), len(not_found))
        #generate excel for not found products
        if len(not_found) > 0:
            tmp_dir = os.path.join(config.get('data_dir'), 'tmp')
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
                
            filename = os.path.join(tmp_dir, 'Not Found Product For Mr [{0}].csv'.format(self.mr_id.name))
            
            with open(filename, 'w', encoding='UTF8', newline='') as f:
                csv_writer = csv.DictWriter(f, fieldnames=file_header)
                csv_writer.writeheader()
                csv_writer.writerows(not_found)
             
            fp = open(filename, "rb")
            data = fp.read()
            data64 = base64.encodebytes(data)
               
            fp.close()
            os.remove(filename)
             
            exported_file_name = 'Not Found Product For Mr [{0}].csv'.format(self.mr_id.name)
            attach_doc = self.env['ir.attachment'].create({'name':exported_file_name , 'datas':data64, 'type':'binary'})
             
            return {
                       'type': 'ir.actions.act_url',
                       'url': '/web/content/%s?download=true' %(str(attach_doc.id)), 
                       'target': 'new'
                   }
    
    def download_csv_template(self):
        csv_file = self.env['ir.attachment'].search([('mimetype', '=', 'application/vnd.ms-excel')])
        self.env.company.csv_template = csv_file 
        template_id = self.env.company.csv_template
        if not template_id:
            raise ValidationError(_('template was not found'))
        
        return  {
                       'type': 'ir.actions.act_url',
                       'url': '/web/content/%s?download=true' %(str(template_id.id)), 
                       'target': 'new'
                }