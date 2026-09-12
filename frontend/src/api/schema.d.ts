export interface paths {
    "/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Live */
        get: operations["live_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ready */
        get: operations["ready_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/r/{code}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Redirect Affiliate Link */
        get: operations["redirect_affiliate_link_r__code__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_v1_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/auth/token": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Token */
        post: operations["token_v1_auth_token_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_v1_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Programs */
        get: operations["list_programs_v1_programs_get"];
        put?: never;
        /** Create Program */
        post: operations["create_program_v1_programs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Program */
        get: operations["get_program_v1_programs__program_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/campaigns": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Campaigns */
        get: operations["list_campaigns_v1_programs__program_id__campaigns_get"];
        put?: never;
        /** Create Campaign */
        post: operations["create_campaign_v1_programs__program_id__campaigns_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/campaigns/{campaign_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Campaign */
        get: operations["get_campaign_v1_campaigns__campaign_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/terms": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Terms */
        get: operations["list_terms_v1_programs__program_id__terms_get"];
        put?: never;
        /** Publish Terms */
        post: operations["publish_terms_v1_programs__program_id__terms_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/commission-plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Commission Plans */
        get: operations["list_commission_plans_v1_programs__program_id__commission_plans_get"];
        put?: never;
        /** Create Commission Plan */
        post: operations["create_commission_plan_v1_programs__program_id__commission_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/commission-plans/{plan_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Commission Plan */
        get: operations["get_commission_plan_v1_commission_plans__plan_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Program Status */
        post: operations["change_program_status_v1_programs__program_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/campaigns/{campaign_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Campaign Status */
        post: operations["change_campaign_status_v1_campaigns__campaign_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/applications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Apply */
        post: operations["apply_v1_programs__program_id__applications_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/applications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Applications */
        get: operations["applications_v1_applications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/applications/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Applications */
        get: operations["my_applications_v1_applications_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/applications/{application_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Application */
        get: operations["get_application_v1_applications__application_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/applications/{application_id}/withdraw": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Withdraw Application */
        post: operations["withdraw_application_v1_applications__application_id__withdraw_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/applications/{application_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Review Application */
        post: operations["review_application_v1_applications__application_id__review_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}/terms-acceptances": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Terms */
        post: operations["accept_terms_v1_memberships__membership_id__terms_acceptances_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Memberships */
        get: operations["my_memberships_v1_memberships_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}/assets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Membership Assets */
        get: operations["membership_assets_v1_memberships__membership_id__assets_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Invitations */
        get: operations["list_invitations_v1_programs__program_id__invitations_get"];
        put?: never;
        /** Create Invitation */
        post: operations["create_invitation_v1_programs__program_id__invitations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/invitations/{token}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Inspect Invitation */
        get: operations["inspect_invitation_v1_invitations__token__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/invitations/{token}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Invitation */
        post: operations["accept_invitation_v1_invitations__token__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/invitations/{invitation_id}/revoke": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Revoke Invitation */
        post: operations["revoke_invitation_v1_invitations__invitation_id__revoke_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/programs/{program_id}/memberships": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Program Memberships */
        get: operations["list_program_memberships_v1_programs__program_id__memberships_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Membership */
        get: operations["get_membership_v1_memberships__membership_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Membership Status */
        post: operations["change_membership_status_v1_memberships__membership_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/campaigns/{campaign_id}/participants": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Campaign Participants */
        get: operations["list_campaign_participants_v1_campaigns__campaign_id__participants_get"];
        put?: never;
        /** Select Campaign Participants */
        post: operations["select_campaign_participants_v1_campaigns__campaign_id__participants_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/campaigns/{campaign_id}/participants/{membership_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Campaign Participant Status */
        post: operations["change_campaign_participant_status_v1_campaigns__campaign_id__participants__membership_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/webhooks/commerce/{brand_slug}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Commerce Webhook */
        post: operations["commerce_webhook_v1_webhooks_commerce__brand_slug__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/commissions/settle": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Settle Commissions */
        post: operations["settle_commissions_v1_commissions_settle_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}/balance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Creator Balance */
        get: operations["creator_balance_v1_memberships__membership_id__balance_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/listening/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Import Social Posts */
        post: operations["import_social_posts_v1_listening_imports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/posts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Social Posts */
        get: operations["list_social_posts_v1_posts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/posts/{content_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Social Post */
        get: operations["get_social_post_v1_posts__content_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/posts/{content_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Review Social Post */
        post: operations["review_social_post_v1_posts__content_id__review_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/orders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Orders */
        get: operations["list_orders_v1_orders_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/orders/{order_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Order */
        get: operations["get_order_v1_orders__order_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/commissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Commissions */
        get: operations["list_commissions_v1_commissions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/memberships/{membership_id}/commissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Membership Commissions */
        get: operations["membership_commissions_v1_memberships__membership_id__commissions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/ledger-entries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Ledger Entries */
        get: operations["list_ledger_entries_v1_ledger_entries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/audit-logs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Audit Logs */
        get: operations["list_audit_logs_v1_audit_logs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/payout-batches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payout Batches */
        get: operations["list_payout_batches_v1_payout_batches_get"];
        put?: never;
        /** Create Payout Batch */
        post: operations["create_payout_batch_v1_payout_batches_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/payout-batches/{batch_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve Payout Batch */
        post: operations["approve_payout_batch_v1_payout_batches__batch_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/payout-batches/{batch_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Payout Batch */
        get: operations["get_payout_batch_v1_payout_batches__batch_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/payouts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payouts */
        get: operations["list_payouts_v1_payouts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/payout-batches/{batch_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Payout Batch */
        post: operations["cancel_payout_batch_v1_payout_batches__batch_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reconciliation/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Reconciliation Runs */
        get: operations["list_reconciliation_runs_v1_reconciliation_runs_get"];
        put?: never;
        /** Reconcile */
        post: operations["reconcile_v1_reconciliation_runs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reconciliation/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Reconciliation Run */
        get: operations["get_reconciliation_run_v1_reconciliation_runs__run_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/findings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Findings */
        get: operations["findings_v1_agent_findings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/findings/{finding_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Finding */
        get: operations["get_finding_v1_agent_findings__finding_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/findings/{finding_id}/dismiss": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Dismiss Finding */
        post: operations["dismiss_finding_v1_agent_findings__finding_id__dismiss_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/findings/{finding_id}/proposals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Propose */
        post: operations["propose_v1_agent_findings__finding_id__proposals_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Proposals */
        get: operations["list_proposals_v1_agent_proposals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals/{proposal_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Proposal */
        get: operations["get_proposal_v1_agent_proposals__proposal_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals/{proposal_id}/gate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Gate */
        post: operations["gate_v1_agent_proposals__proposal_id__gate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals/{proposal_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_v1_agent_proposals__proposal_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals/{proposal_id}/reject": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reject */
        post: operations["reject_v1_agent_proposals__proposal_id__reject_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/agent/proposals/{proposal_id}/execute": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Execute */
        post: operations["execute_v1_agent_proposals__proposal_id__execute_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reports/programs/{program_id}/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Program Overview */
        get: operations["program_overview_v1_reports_programs__program_id__overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reports/campaigns/{campaign_id}/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Campaign Overview */
        get: operations["campaign_overview_v1_reports_campaigns__campaign_id__overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reports/memberships/{membership_id}/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Membership Overview */
        get: operations["membership_overview_v1_reports_memberships__membership_id__overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** ApplicationCreateRequest */
        ApplicationCreateRequest: {
            /**
             * Motivation
             * @default
             */
            motivation: string;
        };
        /** ApplicationDetailResponse */
        ApplicationDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Creator Id
             * Format: uuid
             */
            creator_id: string;
            /** Source */
            source: string;
            status: components["schemas"]["ApplicationStatus"];
            /** Motivation */
            motivation: string;
            /** Review Note */
            review_note: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Program Name */
            program_name: string;
            creator: components["schemas"]["CreatorSummary"];
        };
        /** ApplicationResponse */
        ApplicationResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Creator Id
             * Format: uuid
             */
            creator_id: string;
            /** Source */
            source: string;
            status: components["schemas"]["ApplicationStatus"];
            /** Motivation */
            motivation: string;
            /** Review Note */
            review_note: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ApplicationReviewRequest */
        ApplicationReviewRequest: {
            /**
             * Decision
             * @enum {string}
             */
            decision: "in_review" | "approved" | "rejected";
            /**
             * Note
             * @default
             */
            note: string;
        };
        /** ApplicationReviewResponse */
        ApplicationReviewResponse: {
            application: components["schemas"]["ApplicationResponse"];
            membership: components["schemas"]["MembershipResponse"] | null;
        };
        /**
         * ApplicationStatus
         * @enum {string}
         */
        ApplicationStatus: "submitted" | "in_review" | "approved" | "rejected" | "withdrawn";
        /** ApplicationWithdrawRequest */
        ApplicationWithdrawRequest: {
            /**
             * Comment
             * @default
             */
            comment: string;
        };
        /** ApprovalRequest */
        ApprovalRequest: {
            /** Comment */
            comment: string;
        };
        /** AssetResponse */
        AssetResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Campaign Id */
            campaign_id: string | null;
            asset_type: components["schemas"]["AssetType"];
            /** Code */
            code: string;
            /** Target Url */
            target_url: string | null;
            /** Active */
            active: boolean;
        };
        /**
         * AssetType
         * @enum {string}
         */
        AssetType: "coupon" | "link";
        /**
         * AttributionReason
         * @enum {string}
         */
        AttributionReason: "coupon" | "last_click" | "unattributed" | "manual";
        /** AuditLogResponse */
        AuditLogResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Actor User Id */
            actor_user_id: string | null;
            /** Action */
            action: string;
            /** Entity Type */
            entity_type: string;
            /**
             * Entity Id
             * Format: uuid
             */
            entity_id: string;
            /** Data */
            data: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** BalanceResponse */
        BalanceResponse: {
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Pending */
            pending: string;
            /** Available */
            available: string;
            /** Reserved */
            reserved: string;
            /** Paid */
            paid: string;
        };
        /** BonusRuleInput */
        BonusRuleInput: {
            /** Name */
            name: string;
            /**
             * Metric
             * @enum {string}
             */
            metric: "gmv" | "orders";
            /** Threshold */
            threshold: number | string;
            /** Amount */
            amount: number | string;
        };
        /** BonusRuleResponse */
        BonusRuleResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Metric */
            metric: string;
            /** Threshold */
            threshold: string;
            /** Amount */
            amount: string;
        };
        /**
         * BrandRole
         * @enum {string}
         */
        BrandRole: "owner" | "ops" | "finance";
        /** CampaignCreateRequest */
        CampaignCreateRequest: {
            /** Name */
            name: string;
            /**
             * Briefing
             * @default
             */
            briefing: string;
            /** Starts At */
            starts_at?: string | null;
            /** Ends At */
            ends_at?: string | null;
        };
        /** CampaignParticipantDetailResponse */
        CampaignParticipantDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Campaign Id
             * Format: uuid
             */
            campaign_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            status: components["schemas"]["CampaignParticipantStatus"];
            /** Selected By */
            selected_by: string | null;
            /**
             * Selected At
             * Format: date-time
             */
            selected_at: string;
            /** Removed At */
            removed_at: string | null;
            /** Version */
            version: number;
            creator: components["schemas"]["CreatorSummary"];
            /** Assets */
            assets: components["schemas"]["AssetResponse"][];
        };
        /** CampaignParticipantResponse */
        CampaignParticipantResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Campaign Id
             * Format: uuid
             */
            campaign_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            status: components["schemas"]["CampaignParticipantStatus"];
            /** Selected By */
            selected_by: string | null;
            /**
             * Selected At
             * Format: date-time
             */
            selected_at: string;
            /** Removed At */
            removed_at: string | null;
            /** Version */
            version: number;
        };
        /**
         * CampaignParticipantStatus
         * @enum {string}
         */
        CampaignParticipantStatus: "selected" | "removed";
        /** CampaignParticipantStatusRequest */
        CampaignParticipantStatusRequest: {
            status: components["schemas"]["CampaignParticipantStatus"];
            /** Comment */
            comment: string;
        };
        /** CampaignParticipantsRequest */
        CampaignParticipantsRequest: {
            /** Membership Ids */
            membership_ids: string[];
        };
        /** CampaignReportResponse */
        CampaignReportResponse: {
            /**
             * Campaign Id
             * Format: uuid
             */
            campaign_id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Gmv */
            gmv: string;
            /** Refunded Gmv */
            refunded_gmv: string;
            /** Net Gmv */
            net_gmv: string;
            /** Orders */
            orders: number;
            /** Selected Creators */
            selected_creators: number;
            /** Approved Posts */
            approved_posts: number;
            /** Social Metrics */
            social_metrics: {
                [key: string]: number;
            };
            /** Commission Accrued */
            commission_accrued: string;
            /** Commission Adjustments */
            commission_adjustments: string;
            /** Net Commission */
            net_commission: string;
        };
        /** CampaignResponse */
        CampaignResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Name */
            name: string;
            status: components["schemas"]["CampaignStatus"];
            /** Briefing */
            briefing: string;
            /** Starts At */
            starts_at: string | null;
            /** Ends At */
            ends_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * CampaignStatus
         * @enum {string}
         */
        CampaignStatus: "draft" | "scheduled" | "active" | "ended" | "cancelled";
        /** CampaignStatusRequest */
        CampaignStatusRequest: {
            status: components["schemas"]["CampaignStatus"];
        };
        /**
         * CommissionKind
         * @enum {string}
         */
        CommissionKind: "sale" | "bonus" | "refund_adjustment";
        /** CommissionPlanCreateRequest */
        CommissionPlanCreateRequest: {
            /** Campaign Id */
            campaign_id?: string | null;
            /** Base Rate */
            base_rate: number | string;
            /**
             * Return Window Days
             * @default 7
             */
            return_window_days: number;
            /**
             * Payout Minimum
             * @default 100.00
             */
            payout_minimum: number | string;
            /**
             * Active From
             * Format: date-time
             */
            active_from: string;
            /** Tiers */
            tiers?: components["schemas"]["CommissionTierInput"][];
            /** Bonuses */
            bonuses?: components["schemas"]["BonusRuleInput"][];
        };
        /** CommissionPlanDetailResponse */
        CommissionPlanDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Campaign Id */
            campaign_id: string | null;
            /** Version */
            version: number;
            /** Base Rate */
            base_rate: string;
            /** Return Window Days */
            return_window_days: number;
            /** Payout Minimum */
            payout_minimum: string;
            /**
             * Active From
             * Format: date-time
             */
            active_from: string;
            /** Tiers */
            tiers: components["schemas"]["CommissionTierResponse"][];
            /** Bonuses */
            bonuses: components["schemas"]["BonusRuleResponse"][];
        };
        /** CommissionPlanResponse */
        CommissionPlanResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Campaign Id */
            campaign_id: string | null;
            /** Version */
            version: number;
            /** Base Rate */
            base_rate: string;
            /** Return Window Days */
            return_window_days: number;
            /** Payout Minimum */
            payout_minimum: string;
            /**
             * Active From
             * Format: date-time
             */
            active_from: string;
        };
        /** CommissionResponse */
        CommissionResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Order Id
             * Format: uuid
             */
            order_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /**
             * Plan Id
             * Format: uuid
             */
            plan_id: string;
            /** Plan Version */
            plan_version: number;
            kind: components["schemas"]["CommissionKind"];
            status: components["schemas"]["CommissionStatus"];
            /** Gross Basis */
            gross_basis: string;
            /** Rate */
            rate: string;
            /** Amount */
            amount: string;
            /** Period Key */
            period_key: string;
            /**
             * Eligible At
             * Format: date-time
             */
            eligible_at: string;
            /** Available At */
            available_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * CommissionStatus
         * @enum {string}
         */
        CommissionStatus: "pending" | "available" | "reversed";
        /** CommissionTierInput */
        CommissionTierInput: {
            /**
             * Threshold Gmv
             * @default 0.00
             */
            threshold_gmv: number | string;
            /** Rate */
            rate: number | string;
        };
        /** CommissionTierResponse */
        CommissionTierResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Threshold Gmv */
            threshold_gmv: string;
            /** Rate */
            rate: string;
        };
        /** ContentEvidenceDetailResponse */
        ContentEvidenceDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            network: components["schemas"]["SocialNetwork"];
            /** External Post Id */
            external_post_id: string;
            /** Membership Id */
            membership_id: string | null;
            status: components["schemas"]["ContentStatus"];
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /** Metrics */
            metrics: {
                [key: string]: unknown;
            };
            /**
             * Brand Id
             * Format: uuid
             */
            brand_id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Campaign Id */
            campaign_id: string | null;
            /** Handle Normalized */
            handle_normalized: string;
            /** Firestore Path */
            firestore_path: string;
            /** Reviewed By */
            reviewed_by: string | null;
            /** Reviewed At */
            reviewed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ContentEvidenceResponse */
        ContentEvidenceResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            network: components["schemas"]["SocialNetwork"];
            /** External Post Id */
            external_post_id: string;
            /** Membership Id */
            membership_id: string | null;
            status: components["schemas"]["ContentStatus"];
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /** Metrics */
            metrics: {
                [key: string]: unknown;
            };
        };
        /** ContentReviewRequest */
        ContentReviewRequest: {
            /**
             * Decision
             * @enum {string}
             */
            decision: "approved" | "rejected";
        };
        /**
         * ContentStatus
         * @enum {string}
         */
        ContentStatus: "detected" | "matched" | "approved" | "rejected";
        /** CreatorRegistrationResponse */
        CreatorRegistrationResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Display Name */
            display_name: string;
            kind: components["schemas"]["UserKind"];
        };
        /** CreatorSummary */
        CreatorSummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Display Name */
            display_name: string;
            /** Socials */
            socials?: components["schemas"]["SocialProfileResponse"][];
        };
        /** FindingDismissRequest */
        FindingDismissRequest: {
            /** Comment */
            comment: string;
        };
        /** FindingResponse */
        FindingResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Run Id
             * Format: uuid
             */
            run_id: string;
            /**
             * Payout Id
             * Format: uuid
             */
            payout_id: string;
            finding_type: components["schemas"]["FindingType"];
            state: components["schemas"]["FindingState"];
            /** Evidence */
            evidence: {
                [key: string]: unknown;
            };
            /** Evidence Hash */
            evidence_hash: string;
            /** Payout Version */
            payout_version: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Resolved At */
            resolved_at: string | null;
        };
        /**
         * FindingState
         * @enum {string}
         */
        FindingState: "open" | "proposed" | "resolved" | "dismissed";
        /**
         * FindingType
         * @enum {string}
         */
        FindingType: "provider_confirmed_internal_unknown" | "provider_missing_internal_unknown" | "amount_mismatch" | "duplicate_provider_transfer" | "ledger_balance_mismatch";
        /** GateResponse */
        GateResponse: {
            proposal: components["schemas"]["ProposalResponse"];
            gate: components["schemas"]["GateRunResponse"];
        };
        /** GateRunResponse */
        GateRunResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Proposal Id
             * Format: uuid
             */
            proposal_id: string;
            /** Result */
            result: string;
            /** Checks */
            checks: {
                [key: string]: unknown;
            }[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HealthResponse */
        HealthResponse: {
            /** Status */
            status: string;
        };
        /** InvitationAcceptResponse */
        InvitationAcceptResponse: {
            invitation: components["schemas"]["InvitationResponse"];
            application: components["schemas"]["ApplicationResponse"];
            membership: components["schemas"]["MembershipResponse"];
        };
        /** InvitationCreateRequest */
        InvitationCreateRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Expires In Hours
             * @default 168
             */
            expires_in_hours: number;
        };
        /** InvitationCreatedResponse */
        InvitationCreatedResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            status: components["schemas"]["InvitationStatus"];
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Used At */
            used_at: string | null;
            /** Revoked At */
            revoked_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Token */
            token: string;
            /** Acceptance Url */
            acceptance_url: string;
        };
        /** InvitationInspectResponse */
        InvitationInspectResponse: {
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Program Name */
            program_name: string;
            /** Brand Name */
            brand_name: string;
            /** Email Hint */
            email_hint: string;
            status: components["schemas"]["InvitationStatus"];
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
        };
        /** InvitationResponse */
        InvitationResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            status: components["schemas"]["InvitationStatus"];
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Used At */
            used_at: string | null;
            /** Revoked At */
            revoked_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * InvitationStatus
         * @enum {string}
         */
        InvitationStatus: "pending" | "accepted" | "expired" | "revoked";
        /**
         * LedgerBucket
         * @enum {string}
         */
        LedgerBucket: "pending" | "available" | "reserved" | "paid";
        /** LedgerEntryResponse */
        LedgerEntryResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Commission Id */
            commission_id: string | null;
            /** Payout Id */
            payout_id: string | null;
            bucket: components["schemas"]["LedgerBucket"];
            entry_type: components["schemas"]["LedgerEntryType"];
            /** Amount */
            amount: string;
            /** Currency */
            currency: string;
            /** Idempotency Key */
            idempotency_key: string;
            /** Description */
            description: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * LedgerEntryType
         * @enum {string}
         */
        LedgerEntryType: "commission_accrued" | "commission_settled" | "commission_reversed" | "payout_reserved" | "payout_confirmed" | "payout_released" | "reconciliation_adjustment";
        /** MeResponse */
        MeResponse: {
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Display Name */
            display_name: string;
            kind: components["schemas"]["UserKind"];
            /** Brand Id */
            brand_id: string | null;
            role: components["schemas"]["BrandRole"] | null;
            /** Socials */
            socials?: components["schemas"]["SocialProfileResponse"][];
        };
        /** MembershipDetailResponse */
        MembershipDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Creator Id
             * Format: uuid
             */
            creator_id: string;
            status: components["schemas"]["MembershipStatus"];
            /** Activated At */
            activated_at: string | null;
            /** Version */
            version: number;
            /** Program Name */
            program_name: string;
            creator: components["schemas"]["CreatorSummary"];
            /** Accepted Terms Version */
            accepted_terms_version: number | null;
            required_terms: components["schemas"]["TermsResponse"] | null;
            /** Assets */
            assets: components["schemas"]["AssetResponse"][];
            balance: components["schemas"]["BalanceResponse"];
        };
        /** MembershipReportResponse */
        MembershipReportResponse: {
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Gmv */
            gmv: string;
            /** Refunded Gmv */
            refunded_gmv: string;
            /** Net Gmv */
            net_gmv: string;
            /** Orders */
            orders: number;
            /** Approved Posts */
            approved_posts: number;
            /** Social Metrics */
            social_metrics: {
                [key: string]: number;
            };
            /** Commission Pending */
            commission_pending: string;
            /** Commission Available */
            commission_available: string;
            /** Commission Reserved */
            commission_reserved: string;
            /** Commission Paid */
            commission_paid: string;
            /** Payouts */
            payouts: {
                [key: string]: number;
            };
        };
        /** MembershipResponse */
        MembershipResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Creator Id
             * Format: uuid
             */
            creator_id: string;
            status: components["schemas"]["MembershipStatus"];
            /** Activated At */
            activated_at: string | null;
            /** Version */
            version: number;
        };
        /**
         * MembershipStatus
         * @enum {string}
         */
        MembershipStatus: "awaiting_terms" | "active" | "paused" | "offboarded";
        /** MembershipStatusRequest */
        MembershipStatusRequest: {
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "paused" | "offboarded";
            /** Comment */
            comment: string;
        };
        /** OrderAttributionResponse */
        OrderAttributionResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Membership Id */
            membership_id: string | null;
            /** Campaign Id */
            campaign_id: string | null;
            /** Coupon Asset Id */
            coupon_asset_id: string | null;
            /** Click Id */
            click_id: string | null;
            reason: components["schemas"]["AttributionReason"];
            /** Signals */
            signals: {
                [key: string]: unknown;
            };
            /**
             * Attributed At
             * Format: date-time
             */
            attributed_at: string;
        };
        /** OrderDetailResponse */
        OrderDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Program Id */
            program_id: string | null;
            /** External Id */
            external_id: string;
            status: components["schemas"]["OrderStatus"];
            /** Gross Amount */
            gross_amount: string;
            /** Refunded Amount */
            refunded_amount: string;
            /** Currency */
            currency: string;
            /** Paid At */
            paid_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            attribution: components["schemas"]["OrderAttributionResponse"] | null;
            /** Commissions */
            commissions: components["schemas"]["CommissionResponse"][];
        };
        /** OrderResponse */
        OrderResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Program Id */
            program_id: string | null;
            /** External Id */
            external_id: string;
            status: components["schemas"]["OrderStatus"];
            /** Gross Amount */
            gross_amount: string;
            /** Refunded Amount */
            refunded_amount: string;
            /** Currency */
            currency: string;
            /** Paid At */
            paid_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * OrderStatus
         * @enum {string}
         */
        OrderStatus: "created" | "paid" | "cancelled" | "partially_refunded" | "refunded";
        /** PageResponse[ApplicationDetailResponse] */
        PageResponse_ApplicationDetailResponse_: {
            /** Items */
            items: components["schemas"]["ApplicationDetailResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[AuditLogResponse] */
        PageResponse_AuditLogResponse_: {
            /** Items */
            items: components["schemas"]["AuditLogResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[CampaignParticipantDetailResponse] */
        PageResponse_CampaignParticipantDetailResponse_: {
            /** Items */
            items: components["schemas"]["CampaignParticipantDetailResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[CampaignResponse] */
        PageResponse_CampaignResponse_: {
            /** Items */
            items: components["schemas"]["CampaignResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[CommissionPlanResponse] */
        PageResponse_CommissionPlanResponse_: {
            /** Items */
            items: components["schemas"]["CommissionPlanResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[CommissionResponse] */
        PageResponse_CommissionResponse_: {
            /** Items */
            items: components["schemas"]["CommissionResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[ContentEvidenceResponse] */
        PageResponse_ContentEvidenceResponse_: {
            /** Items */
            items: components["schemas"]["ContentEvidenceResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[FindingResponse] */
        PageResponse_FindingResponse_: {
            /** Items */
            items: components["schemas"]["FindingResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[InvitationResponse] */
        PageResponse_InvitationResponse_: {
            /** Items */
            items: components["schemas"]["InvitationResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[LedgerEntryResponse] */
        PageResponse_LedgerEntryResponse_: {
            /** Items */
            items: components["schemas"]["LedgerEntryResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[MembershipDetailResponse] */
        PageResponse_MembershipDetailResponse_: {
            /** Items */
            items: components["schemas"]["MembershipDetailResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[MembershipResponse] */
        PageResponse_MembershipResponse_: {
            /** Items */
            items: components["schemas"]["MembershipResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[OrderResponse] */
        PageResponse_OrderResponse_: {
            /** Items */
            items: components["schemas"]["OrderResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[PayoutBatchResponse] */
        PageResponse_PayoutBatchResponse_: {
            /** Items */
            items: components["schemas"]["PayoutBatchResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[PayoutItemResponse] */
        PageResponse_PayoutItemResponse_: {
            /** Items */
            items: components["schemas"]["PayoutItemResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[ProgramResponse] */
        PageResponse_ProgramResponse_: {
            /** Items */
            items: components["schemas"]["ProgramResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[ProposalResponse] */
        PageResponse_ProposalResponse_: {
            /** Items */
            items: components["schemas"]["ProposalResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[ReconciliationRunResponse] */
        PageResponse_ReconciliationRunResponse_: {
            /** Items */
            items: components["schemas"]["ReconciliationRunResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PageResponse[TermsResponse] */
        PageResponse_TermsResponse_: {
            /** Items */
            items: components["schemas"]["TermsResponse"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** PayoutBatchCancelRequest */
        PayoutBatchCancelRequest: {
            /** Comment */
            comment: string;
        };
        /** PayoutBatchCreateRequest */
        PayoutBatchCreateRequest: {
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Cutoff At
             * Format: date-time
             */
            cutoff_at: string;
            /** @default success */
            scenario: components["schemas"]["ProviderScenario"];
        };
        /** PayoutBatchDetailResponse */
        PayoutBatchDetailResponse: {
            batch: components["schemas"]["PayoutBatchResponse"];
            /** Payouts */
            payouts: components["schemas"]["PayoutItemResponse"][];
        };
        /** PayoutBatchResponse */
        PayoutBatchResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Cutoff At
             * Format: date-time
             */
            cutoff_at: string;
            status: components["schemas"]["PayoutBatchStatus"];
            /**
             * Created By
             * Format: uuid
             */
            created_by: string;
            /** Approved By */
            approved_by: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * PayoutBatchStatus
         * @enum {string}
         */
        PayoutBatchStatus: "draft" | "approved" | "processing" | "completed" | "partially_failed" | "cancelled";
        /** PayoutItemResponse */
        PayoutItemResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Batch Id
             * Format: uuid
             */
            batch_id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Amount */
            amount: string;
            /** Currency */
            currency: string;
            status: components["schemas"]["PayoutStatus"];
            /** Provider Reference */
            provider_reference: string | null;
            /** Version */
            version: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * PayoutStatus
         * @enum {string}
         */
        PayoutStatus: "draft" | "pending" | "confirmed" | "failed" | "unknown";
        /** ProgramCreateRequest */
        ProgramCreateRequest: {
            /** Name */
            name: string;
            /** Slug */
            slug: string;
            /**
             * Attribution Window Days
             * @default 30
             */
            attribution_window_days: number;
            /**
             * Return Window Days
             * @default 7
             */
            return_window_days: number;
            /**
             * Payout Minimum
             * @default 100.00
             */
            payout_minimum: number | string;
        };
        /** ProgramResponse */
        ProgramResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Brand Id
             * Format: uuid
             */
            brand_id: string;
            /** Name */
            name: string;
            /** Slug */
            slug: string;
            status: components["schemas"]["ProgramStatus"];
            /** Attribution Window Days */
            attribution_window_days: number;
            /** Return Window Days */
            return_window_days: number;
            /** Payout Minimum */
            payout_minimum: string;
            /** Currency */
            currency: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ProgramStatus
         * @enum {string}
         */
        ProgramStatus: "draft" | "active" | "paused" | "closed";
        /** ProgramStatusRequest */
        ProgramStatusRequest: {
            status: components["schemas"]["ProgramStatus"];
        };
        /**
         * ProposalAction
         * @enum {string}
         */
        ProposalAction: "confirm_payout" | "mark_failed_release" | "compensating_adjustment" | "manual_review";
        /** ProposalDetailResponse */
        ProposalDetailResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Finding Id
             * Format: uuid
             */
            finding_id: string;
            action: components["schemas"]["ProposalAction"];
            state: components["schemas"]["ProposalState"];
            /** Rationale */
            rationale: string;
            /** Risk */
            risk: string;
            /** Proposed Changes */
            proposed_changes: {
                [key: string]: unknown;
            };
            /** Payout Version */
            payout_version: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Evidence Hash */
            evidence_hash: string;
            /** Approved By */
            approved_by: string | null;
            /** Approval Comment */
            approval_comment: string | null;
            /** Approved At */
            approved_at: string | null;
            /** Rejected By */
            rejected_by: string | null;
            /** Rejection Comment */
            rejection_comment: string | null;
            /** Rejected At */
            rejected_at: string | null;
            /** Executed At */
            executed_at: string | null;
            /** Gates */
            gates: components["schemas"]["GateRunResponse"][];
        };
        /** ProposalResponse */
        ProposalResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Finding Id
             * Format: uuid
             */
            finding_id: string;
            action: components["schemas"]["ProposalAction"];
            state: components["schemas"]["ProposalState"];
            /** Rationale */
            rationale: string;
            /** Risk */
            risk: string;
            /** Proposed Changes */
            proposed_changes: {
                [key: string]: unknown;
            };
            /** Payout Version */
            payout_version: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ProposalState
         * @enum {string}
         */
        ProposalState: "draft" | "gated" | "blocked" | "approved" | "rejected" | "executed" | "stale";
        /**
         * ProviderScenario
         * @enum {string}
         */
        ProviderScenario: "success" | "failure" | "timeout_before" | "timeout_after";
        /** ReadinessResponse */
        ReadinessResponse: {
            /** Status */
            status: string;
            /** Database */
            database: string;
        };
        /** ReconciliationRunResponse */
        ReconciliationRunResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Brand Id
             * Format: uuid
             */
            brand_id: string;
            /**
             * Started By
             * Format: uuid
             */
            started_by: string;
            /** Status */
            status: string;
            /**
             * Started At
             * Format: date-time
             */
            started_at: string;
            /** Completed At */
            completed_at: string | null;
            /** Summary */
            summary: {
                [key: string]: unknown;
            };
        };
        /**
         * ReconciliationRunStatus
         * @enum {string}
         */
        ReconciliationRunStatus: "running" | "completed" | "failed";
        /** RegisterCreatorRequest */
        RegisterCreatorRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
            /** Display Name */
            display_name: string;
            /** Socials */
            socials?: components["schemas"]["SocialProfileInput"][];
        };
        /** RejectRequest */
        RejectRequest: {
            /** Comment */
            comment: string;
        };
        /** ReportOverviewResponse */
        ReportOverviewResponse: {
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Gmv */
            gmv: string;
            /** Refunded Gmv */
            refunded_gmv: string;
            /** Net Gmv */
            net_gmv: string;
            /** Orders */
            orders: number;
            /** Attributed Orders */
            attributed_orders: number;
            /** Active Creators */
            active_creators: number;
            /** Approved Posts */
            approved_posts: number;
            /** Commission Pending */
            commission_pending: string;
            /** Commission Available */
            commission_available: string;
            /** Commission Reserved */
            commission_reserved: string;
            /** Commission Paid */
            commission_paid: string;
            /** Payouts */
            payouts: {
                [key: string]: number;
            };
            /** Social Metrics */
            social_metrics?: {
                [key: string]: number;
            };
        };
        /** SettlementRequest */
        SettlementRequest: {
            /** As Of */
            as_of?: string | null;
        };
        /** SettlementResponse */
        SettlementResponse: {
            /** Settled */
            settled: number;
        };
        /** SocialImportRequest */
        SocialImportRequest: {
            /** Posts */
            posts: components["schemas"]["SocialPostInput"][];
        };
        /** SocialImportResponse */
        SocialImportResponse: {
            /**
             * Status
             * @constant
             */
            status: "queued";
            /** Posts */
            posts: number;
        };
        /**
         * SocialNetwork
         * @enum {string}
         */
        SocialNetwork: "instagram" | "tiktok";
        /** SocialPostInput */
        SocialPostInput: {
            network: components["schemas"]["SocialNetwork"];
            /** External Post Id */
            external_post_id: string;
            /** Handle */
            handle: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Campaign Id */
            campaign_id?: string | null;
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /**
             * Caption
             * @default
             */
            caption: string;
            /** Url */
            url?: string | null;
            /** Metrics */
            metrics?: {
                [key: string]: number;
            };
        };
        /** SocialProfileInput */
        SocialProfileInput: {
            network: components["schemas"]["SocialNetwork"];
            /** Handle */
            handle: string;
        };
        /** SocialProfileResponse */
        SocialProfileResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            network: components["schemas"]["SocialNetwork"];
            /** Handle */
            handle: string;
            /** Handle Normalized */
            handle_normalized: string;
            /** Verified */
            verified: boolean;
        };
        /** TermsAcceptanceRequest */
        TermsAcceptanceRequest: {
            /**
             * Terms Id
             * Format: uuid
             */
            terms_id: string;
        };
        /** TermsAcceptanceResponse */
        TermsAcceptanceResponse: {
            membership: components["schemas"]["MembershipResponse"];
            /** Assets */
            assets: components["schemas"]["AssetResponse"][];
        };
        /** TermsCreateRequest */
        TermsCreateRequest: {
            /** Content */
            content: string;
            /**
             * Required
             * @default true
             */
            required: boolean;
        };
        /** TermsResponse */
        TermsResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Program Id
             * Format: uuid
             */
            program_id: string;
            /** Version */
            version: number;
            /** Content */
            content: string;
            /** Required */
            required: boolean;
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
        };
        /** TokenRequest */
        TokenRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
            /** Brand Slug */
            brand_slug?: string | null;
        };
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             * @constant
             */
            token_type: "bearer";
            /** Expires In */
            expires_in: number;
        };
        /**
         * UserKind
         * @enum {string}
         */
        UserKind: "staff" | "creator";
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** WebhookResponse */
        WebhookResponse: {
            /** Event Id */
            event_id: string;
            /** Order Id */
            order_id: string | null;
            /** Status */
            status: string;
            /**
             * Duplicate
             * @default false
             */
            duplicate: boolean;
            /** Attribution */
            attribution?: string | null;
            /** Commission */
            commission?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    live_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponse"];
                };
            };
        };
    };
    ready_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessResponse"];
                };
            };
        };
    };
    redirect_affiliate_link_r__code__get: {
        parameters: {
            query?: {
                visitor?: string | null;
            };
            header?: never;
            path: {
                code: string;
            };
            cookie?: {
                creatorops_visitor?: string | null;
            };
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_v1_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterCreatorRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CreatorRegistrationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    token_v1_auth_token_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TokenRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    me_v1_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeResponse"];
                };
            };
        };
    };
    list_programs_v1_programs_get: {
        parameters: {
            query?: {
                program_status?: components["schemas"]["ProgramStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ProgramResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_program_v1_programs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProgramCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProgramResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_program_v1_programs__program_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProgramResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_campaigns_v1_programs__program_id__campaigns_get: {
        parameters: {
            query?: {
                campaign_status?: components["schemas"]["CampaignStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_CampaignResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_campaign_v1_programs__program_id__campaigns_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CampaignCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_campaign_v1_campaigns__campaign_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                campaign_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_terms_v1_programs__program_id__terms_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_TermsResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    publish_terms_v1_programs__program_id__terms_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TermsCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TermsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_commission_plans_v1_programs__program_id__commission_plans_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_CommissionPlanResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_commission_plan_v1_programs__program_id__commission_plans_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommissionPlanCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CommissionPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_commission_plan_v1_commission_plans__plan_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CommissionPlanDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_program_status_v1_programs__program_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProgramStatusRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProgramResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_campaign_status_v1_campaigns__campaign_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                campaign_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CampaignStatusRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    apply_v1_programs__program_id__applications_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplicationCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApplicationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    applications_v1_applications_get: {
        parameters: {
            query?: {
                application_status?: components["schemas"]["ApplicationStatus"] | null;
                program_id?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ApplicationDetailResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_applications_v1_applications_me_get: {
        parameters: {
            query?: {
                application_status?: components["schemas"]["ApplicationStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ApplicationDetailResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_application_v1_applications__application_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApplicationDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    withdraw_application_v1_applications__application_id__withdraw_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplicationWithdrawRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApplicationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_application_v1_applications__application_id__review_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplicationReviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApplicationReviewResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    accept_terms_v1_memberships__membership_id__terms_acceptances_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TermsAcceptanceRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TermsAcceptanceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_memberships_v1_memberships_me_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_MembershipResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    membership_assets_v1_memberships__membership_id__assets_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_invitations_v1_programs__program_id__invitations_get: {
        parameters: {
            query?: {
                invitation_status?: components["schemas"]["InvitationStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_InvitationResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_invitation_v1_programs__program_id__invitations_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InvitationCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationCreatedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    inspect_invitation_v1_invitations__token__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationInspectResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    accept_invitation_v1_invitations__token__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationAcceptResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    revoke_invitation_v1_invitations__invitation_id__revoke_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invitation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RejectRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_program_memberships_v1_programs__program_id__memberships_get: {
        parameters: {
            query?: {
                membership_status?: components["schemas"]["MembershipStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_MembershipDetailResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_membership_v1_memberships__membership_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MembershipDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_membership_status_v1_memberships__membership_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MembershipStatusRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MembershipResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_campaign_participants_v1_campaigns__campaign_id__participants_get: {
        parameters: {
            query?: {
                participant_status?: components["schemas"]["CampaignParticipantStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                campaign_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_CampaignParticipantDetailResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    select_campaign_participants_v1_campaigns__campaign_id__participants_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                campaign_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CampaignParticipantsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignParticipantResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_campaign_participant_status_v1_campaigns__campaign_id__participants__membership_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                campaign_id: string;
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CampaignParticipantStatusRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignParticipantResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    commerce_webhook_v1_webhooks_commerce__brand_slug__post: {
        parameters: {
            query?: never;
            header?: {
                "X-Webhook-Signature"?: string | null;
            };
            path: {
                brand_slug: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    settle_commissions_v1_commissions_settle_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SettlementRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettlementResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    creator_balance_v1_memberships__membership_id__balance_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BalanceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    import_social_posts_v1_listening_imports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SocialImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SocialImportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_social_posts_v1_posts_get: {
        parameters: {
            query?: {
                content_status?: components["schemas"]["ContentStatus"] | null;
                program_id?: string | null;
                campaign_id?: string | null;
                membership_id?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ContentEvidenceResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_social_post_v1_posts__content_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentEvidenceDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_social_post_v1_posts__content_id__review_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                content_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContentReviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentEvidenceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_orders_v1_orders_get: {
        parameters: {
            query?: {
                program_id?: string | null;
                campaign_id?: string | null;
                membership_id?: string | null;
                order_status?: components["schemas"]["OrderStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_OrderResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_order_v1_orders__order_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrderDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_commissions_v1_commissions_get: {
        parameters: {
            query?: {
                program_id?: string | null;
                membership_id?: string | null;
                commission_status?: components["schemas"]["CommissionStatus"] | null;
                commission_kind?: components["schemas"]["CommissionKind"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_CommissionResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    membership_commissions_v1_memberships__membership_id__commissions_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_CommissionResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_ledger_entries_v1_ledger_entries_get: {
        parameters: {
            query?: {
                program_id?: string | null;
                membership_id?: string | null;
                bucket?: components["schemas"]["LedgerBucket"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_LedgerEntryResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_audit_logs_v1_audit_logs_get: {
        parameters: {
            query?: {
                actor_user_id?: string | null;
                action?: string | null;
                entity_type?: string | null;
                from_at?: string | null;
                to_at?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_AuditLogResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_payout_batches_v1_payout_batches_get: {
        parameters: {
            query?: {
                program_id?: string | null;
                batch_status?: components["schemas"]["PayoutBatchStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_PayoutBatchResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_payout_batch_v1_payout_batches_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PayoutBatchCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayoutBatchDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_payout_batch_v1_payout_batches__batch_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayoutBatchDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_payout_batch_v1_payout_batches__batch_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayoutBatchDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_payouts_v1_payouts_get: {
        parameters: {
            query?: {
                program_id?: string | null;
                batch_id?: string | null;
                membership_id?: string | null;
                payout_status?: components["schemas"]["PayoutStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_PayoutItemResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cancel_payout_batch_v1_payout_batches__batch_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PayoutBatchCancelRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayoutBatchDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_reconciliation_runs_v1_reconciliation_runs_get: {
        parameters: {
            query?: {
                run_status?: components["schemas"]["ReconciliationRunStatus"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ReconciliationRunResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reconcile_v1_reconciliation_runs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReconciliationRunResponse"];
                };
            };
        };
    };
    get_reconciliation_run_v1_reconciliation_runs__run_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReconciliationRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    findings_v1_agent_findings_get: {
        parameters: {
            query?: {
                finding_state?: components["schemas"]["FindingState"] | null;
                finding_type?: components["schemas"]["FindingType"] | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_FindingResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_finding_v1_agent_findings__finding_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                finding_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FindingResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dismiss_finding_v1_agent_findings__finding_id__dismiss_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                finding_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FindingDismissRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FindingResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    propose_v1_agent_findings__finding_id__proposals_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                finding_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_proposals_v1_agent_proposals_get: {
        parameters: {
            query?: {
                proposal_state?: components["schemas"]["ProposalState"] | null;
                finding_id?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PageResponse_ProposalResponse_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_proposal_v1_agent_proposals__proposal_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    gate_v1_agent_proposals__proposal_id__gate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GateResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_v1_agent_proposals__proposal_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reject_v1_agent_proposals__proposal_id__reject_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RejectRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    execute_v1_agent_proposals__proposal_id__execute_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    program_overview_v1_reports_programs__program_id__overview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                program_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportOverviewResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    campaign_overview_v1_reports_campaigns__campaign_id__overview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                campaign_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CampaignReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    membership_overview_v1_reports_memberships__membership_id__overview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MembershipReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
