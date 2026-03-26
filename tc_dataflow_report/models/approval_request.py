from odoo import models


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    def action_approve(self, approver=None):
        result = super().action_approve(approver=approver)
        self.env["tc.daily.upload.file"].sudo().search([("approval_request_id", "in", self.ids)])._sync_with_approval_request()
        return result

    def action_refuse(self, approver=None):
        result = super().action_refuse(approver=approver)
        self.env["tc.daily.upload.file"].sudo().search([("approval_request_id", "in", self.ids)])._sync_with_approval_request()
        return result

    def _action_force_approval(self):
        result = super()._action_force_approval()
        self.env["tc.daily.upload.file"].sudo().search([("approval_request_id", "in", self.ids)])._sync_with_approval_request()
        return result
