"""USAC Form 470 competitive bidding dataset (application grain)."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class Form470(DatasetMeta):
    """Form 470 competitive bidding filings, at application grain.

    Answers "did this applicant post a Form 470 for this funding year, and was
    it certified?". Filtered by ``ben`` and ``funding_year``.

    Dataset: https://opendata.usac.org/resource/jp7a-89nd

    .. note::
       This is the application-grain dataset. Its sibling ``jt8s-3q52``
       ("E-Rate FCC Form 470 Tool Data") is line-level, one row per service
       request, so a single form yields many rows there and any "did they
       file?" question needs a dedupe first. Use this class for filing
       questions and ``jt8s-3q52`` only when the requested services matter.

    .. warning::
       Application grain does not mean one row per form. The grain is one row
       per form **version**: a filing modified after certification appears
       twice, as ``form_version='Original'`` and ``form_version='Current'``,
       identical in every other field. Counting rows therefore overstates
       filings. As at 2026-07-26 the dataset held 283,990 rows for 249,759
       distinct ``application_number`` values, 249,761 ``Original`` and 34,229
       ``Current``, so roughly one filing in seven has been revised.

       Every filing has an ``Original`` row, so :meth:`originals_only` is the
       filter that makes a row count mean "filings". ``f470_status`` never
       disagrees between the two versions of a filing (verified across the
       whole dataset on 2026-07-26), so status questions are safe either way;
       prefer the ``Current`` row when you need the revised values of any
       other field. Note also that one applicant can legitimately file several
       distinct Form 470s in a single funding year, so ``(ben, funding_year)``
       is not a unique key even after collapsing versions.

    .. warning::
       ``f470_number`` is a Socrata ``url`` column, so it deserialises as a
       nested object rather than a string. Reading it as text yields a dict.

    .. warning::
       There is no consultant column here, which is deliberate on USAC's part
       and cleaner than the alternative: ``jt8s-3q52`` carries
       ``consulting_firm_data`` as a composite string of the form
       ``{Firm Name|16043595|555-555-5555|inbox@example.com}``, so filtering it
       by consultant registration number silently returns nothing. To find a
       consultant's filings, join through
       :class:`~usac_data.datasets.Consultants` (``x5px-esft``) instead.

    .. warning::
       The contact and authorised-person fields below are personal data:
       names, addresses, phone numbers and email addresses of identifiable
       people. Select them only when the use case needs them.

    Field names were verified against the live column metadata on 2026-07-26.
    """

    dataset_id = "jp7a-89nd"
    name = (
        "E-Rate Open Competitive Bidding: Basic Information "
        "(FCC Form 470 and Related Information)"
    )
    description = "Form 470 competitive bidding filings at application grain"

    # -- Applicant (note: ben here, as in Form471, not billed_entity_number) --
    ben = "ben"
    billed_entity_name = "billed_entity_name"
    applicant_type = "applicant_type"
    organization_type = "organization_type"
    organization_status = "organization_status"
    billed_entity_state = "billed_entity_state"
    number_of_eligible_entities = "number_of_eligible_entities"

    # -- Filing lifecycle --
    application_number = "application_number"
    # Socrata `url` column: deserialises as a nested object, not a string.
    f470_number = "f470_number"
    form_nickname = "form_nickname"
    funding_year = "funding_year"
    f470_status = "f470_status"
    allowable_contract_date = "allowable_contract_date"
    created_datetime = "created_datetime"
    certified_datetime = "certified_datetime"
    last_modified_datetime = "last_modified_datetime"

    # -- Service description --
    category_one_description = "category_one_description"
    category_two_description = "category_two_description"
    rfp_identifier = "rfp_identifier"
    statewide_state = "statewide_state"
    installment_type = "installment_type"
    state_or_local_restrictions = "state_or_local_restrictions"

    # -- Contact block (personal data) --
    contact_name = "contact_name"
    contact_email = "contact_email"
    contact_phone = "contact_phone"
    technical_contact_name = "technical_contact_name"
    technical_contact_email = "technical_contact_email"
    technical_contact_phone = "technical_contact_phone"

    # -- Authorised person block (personal data) --
    authorized_person_name = "authorized_person_name"
    authorized_person_title = "authorized_person_title"
    authorized_person_email = "authorized_person_email"
    authorized_person_phone = "authorized_person_phone"
    authorized_person_employer = "authorized_person_employer"

    @classmethod
    def for_ben(cls, ben: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a billed entity number."""
        return SoQLBuilder().where(ben=ben)

    @classmethod
    def for_year(cls, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a funding year."""
        return SoQLBuilder().where(funding_year=year)

    @classmethod
    def for_ben_year(cls, ben: int | str, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to one applicant in one funding year."""
        return SoQLBuilder().where(ben=ben, funding_year=year)

    @classmethod
    def originals_only(cls) -> SoQLBuilder:
        """Convenience: collapse form versions to one row per filing.

        See the class docstring: a form modified after certification appears
        twice, once as ``Original`` and once as ``Current``. Every filing has
        an ``Original`` row, so this is the filter that makes row counts mean
        "filings". Use ``form_version='Current'`` instead when you need the
        post-modification values of a form that was revised.
        """
        return SoQLBuilder().where(form_version="Original")
