/* @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { AccountTypeSelection as OriginalAccountTypeSelection } from "@account/components/account_type_selection/account_type_selection";

export class CustomAccountTypeSelection extends OriginalAccountTypeSelection {
    setup() {
        super.setup();
        // Initialize options first from the parent
        this.customAccountTypes = [];
        this.customAccountTypesMap = new Map();
        
        // Now load custom types
        this.loadCustomAccountTypes();
    }
    
    async loadCustomAccountTypes() {
        try {
            const result = await this.orm.call(
                'custom.account.type',
                'search_read',
                [[]],
                { fields: ['id', 'name', 'code', 'internal_group'] }
            );
           
            // Store the full custom type data for internal_group lookup
            this.customAccountTypes = result.map(type => [type.code, type.name]);
            result.forEach(type => {
                this.customAccountTypesMap.set(type.code, type.internal_group);
            });
            
            // Update options after loading is complete
            this.options = [...this.options, ...this.customAccountTypes];
            // Force a re-render after loading
            this.render();
        } catch (error) {
            console.error("Failed to load custom account types:", error);
        }
    }
    
    get hierarchyOptions() {
        const opts = this.options || [];
        return [
            { name: _t('Balance Sheet') },
            { name: _t('Assets'), children: opts.filter(x => x[0] && (x[0].startsWith('asset') || this.getInternalGroup(x[0]) === 'asset')) },
            { name: _t('Liabilities'), children: opts.filter(x => x[0] && (x[0].startsWith('liability') || this.getInternalGroup(x[0]) === 'liability')) },
            { name: _t('Equity'), children: opts.filter(x => x[0] && (x[0].startsWith('equity') || this.getInternalGroup(x[0]) === 'equity')) },
            { name: _t('Profit & Loss') },
            { name: _t('Income'), children: opts.filter(x => x[0] && (x[0].startsWith('income') || this.getInternalGroup(x[0]) === 'income')) },
            { name: _t('Expense'), children: opts.filter(x => x[0] && (x[0].startsWith('expense') || this.getInternalGroup(x[0]) === 'expense')) },
            { name: _t('Other'), children: opts.filter(x => x[0] && (x[0].startsWith('off_balance') || this.getInternalGroup(x[0]) === 'off_balance')) },
        ];
    }
    
    getInternalGroup(code) {
        return this.customAccountTypesMap.get(code) || null;
    }
}

CustomAccountTypeSelection.template = "account.CustomAccountTypeSelection";

export const customAccountTypeSelection = {
    ...registry.category("fields").get("account_type_selection"),
    component: CustomAccountTypeSelection,
};

registry.category("fields").add("custom_account_type_selection", customAccountTypeSelection);