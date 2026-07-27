"""USAC invoices and authorized disbursements dataset."""

from __future__ import annotations

from collections.abc import Sequence

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder

# erate-shepherd's production batch size. FRN lists are typically long and the
# whole list goes into a single SoQL IN clause, so batching keeps the request
# URL under Socrata's length limit.
DEFAULT_FRN_BATCH_SIZE = 80


class Disbursements(DatasetMeta):
    """Invoice line items and authorized disbursements (FCC Forms 472 and 474).

    This is the "what was actually paid out" dataset, as opposed to
    :class:`~usac_data.datasets.RecipientCommitments` ("what was committed").

    Dataset: https://opendata.usac.org/resource/jpiu-tj8h

    .. warning::
       Records are line level, not FRN level. One FRN yields many rows, so
       aggregate by ``funding_request_number`` before comparing against a
       committed amount.

    .. warning::
       ``inv_line_item_status`` is uniformly ``SENT TO USAC`` and carries no
       signal. Use ``approved_inv_line_amt`` to determine what was actually
       authorized, and note that it differs from ``requested_inv_line_amt``.

    .. warning::
       ``consultant_registration_number`` is frequently null here, so querying
       by consultant silently under-reports. Resolve the consultant's FRNs
       through :class:`~usac_data.datasets.Consultants` and query this dataset
       by FRN instead, which is what :meth:`for_frns` is for.

    ``invoice_type`` distinguishes Service Provider invoices (SPI, Form 474)
    from Applicant invoices (BEAR, Form 472).

    Field names were verified against the live column metadata on 2026-07-26.
    """

    dataset_id = "jpiu-tj8h"
    name = "E-Rate Invoices and Authorized Disbursements (FCC Forms 472 and 474)"
    description = "Invoice line items and authorized disbursements"

    # -- Invoice identity --
    invoice_id = "invoice_id"
    # SPI (service provider, Form 474) vs BEAR (applicant, Form 472).
    invoice_type = "invoice_type"
    submission_method = "submission_method"
    form_nickname = "form_nickname"
    inv_line_num = "inv_line_num"
    # Uniformly "SENT TO USAC". Carries no signal; use approved_inv_line_amt.
    inv_line_item_status = "inv_line_item_status"

    # -- Application keys --
    funding_year = "funding_year"
    form_471_app_num = "form_471_app_num"
    funding_request_number = "funding_request_number"
    service_type = "service_type"
    chosen_category_of_service = "chosen_category_of_service"

    # -- Applicant --
    billed_entity_number = "billed_entity_number"
    billed_entity_name = "billed_entity_name"
    billed_entity_state = "billed_entity_state"
    applicant_type = "applicant_type"
    form_498_applicant_id = "form_498_applicant_id"
    billed_entity_number_applicant_invoice = "billed_entity_number_applicant_invoice"
    billed_entity_name_applicant_invoice = "billed_entity_name_applicant_invoice"

    # -- Service provider --
    inv_service_provider_id_number_spin = "inv_service_provider_id_number_spin"
    inv_service_provider_name = "inv_service_provider_name"

    # -- Consultant (frequently null; query by FRN instead) --
    consultant_registration_number = "consultant_registration_number"
    consultant_name = "consultant_name"

    # -- Dates --
    inv_crtfctn_dt = "inv_crtfctn_dt"
    inv_received_date = "inv_received_date"
    invoice_delivery_deadline_dt = "invoice_delivery_deadline_dt"
    customer_billed_dt = "customer_billed_dt"
    shipping_date_to_customer = "shipping_date_to_customer"
    inv_line_completion_date = "inv_line_completion_date"

    # -- Amounts --
    inv_total_requested_amt = "inv_total_requested_amt"
    inv_tot_undiscounted_amt = "inv_tot_undiscounted_amt"
    discount_rate = "discount_rate"
    requested_inv_line_amt = "requested_inv_line_amt"
    # The authorized amount. This is the field that matters.
    approved_inv_line_amt = "approved_inv_line_amt"
    bill_frequency = "bill_frequency"

    # -- Decision --
    reimb_request_decision_codes = "reimb_request_decision_codes"
    reimb_request_decision_descrip = "reimb_request_decision_descrip"
    reimb_request_decision_descrip_plain = "reimb_request_decision_descrip_plain"

    @classmethod
    def for_frns(
        cls,
        # Sequence, not list: list is invariant, so a list[str] of FRNs (the
        # normal way to call this) would not type-check against list[int | str].
        frns: Sequence[int | str],
        batch_size: int = DEFAULT_FRN_BATCH_SIZE,
    ) -> list[SoQLBuilder]:
        """Build one query per batch of funding request numbers.

        FRN lists are typically long enough that a single ``IN`` clause would
        overrun the request URL, so this returns a list of builders to be
        issued separately and concatenated by the caller.

        An empty ``frns`` yields no builders, because ``IN ()`` is a SoQL
        syntax error rather than an empty result.
        """
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")
        return [
            SoQLBuilder().where_in(cls.funding_request_number, list(batch))
            for batch in (
                frns[i : i + batch_size] for i in range(0, len(frns), batch_size)
            )
        ]
