import hashlib
import json
import os
import time
from datetime import datetime

import streamlit as st

from audit import get_history, log_event
from classifier import classify_document
from database import (
    create_database,
    document_hash_exists,
    get_all_documents,
    get_audit_history,
    get_document_by_id,
    get_filtered_documents,
    get_metrics,
    insert_document,
    update_document_fields,
    update_document_workflow,
)
from extractor import extract_fields
from processor import process_document
from storage_manager import get_storage_path
from validator import validate_document
from workflow import (
    LOW_CONFIDENCE_THRESHOLD,
    apply_rules,
    can_transition,
    review_decision,
    transition_or_raise,
)

st.set_page_config(
    page_title="AI Document Intelligence - Week 5",
    page_icon="📄",
    layout="wide",
)

create_database()


def calculate_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


def parse_json(value, default):
    if not value:
        return default
    try:
        result = json.loads(value)
        return result
    except (TypeError, json.JSONDecodeError):
        return default


def transition_document(document_id, new_state, action, reason=""):
    document = get_document_by_id(document_id)
    if not document:
        raise ValueError("Document not found.")
    previous = document["workflow_state"]
    transition_or_raise(previous, new_state)
    update_document_workflow(
        document_id,
        workflow_state=new_state,
        review_reason=reason if new_state == "Needs Review" else document.get("review_reason", ""),
        last_action=action,
    )
    log_event(document_id, action, previous, new_state, reason)
    return new_state


def process_existing_document(document_id):
    document = get_document_by_id(document_id)
    if not document:
        raise ValueError("Document not found.")
    if document["workflow_state"] in {"Approved", "Rejected", "Completed"}:
        raise ValueError(f"{document['workflow_state']} documents are not reprocessed by batch workflow.")

    transition_document(document_id, "Processing", "Processing started")
    started = time.perf_counter()

    try:
        text = document.get("text_preview", "") or ""
        # Stored text_preview is only 500 chars in Week 4. If the file exists,
        # read and process it again to get the full text.
        path = document.get("file_path", "")
        if os.path.exists(path):
            with open(path, "rb") as file:
                file_bytes = file.read()
            text = process_document(file_bytes, document["original_filename"])

        if not text:
            elapsed = time.perf_counter() - started
            update_document_workflow(
                document_id,
                workflow_state="Needs Review",
                validation_errors=["No readable text could be extracted."],
                review_reason="Document text could not be read.",
                last_action="Processing failed",
                processing_time=elapsed,
                processing_error=1,
            )
            log_event(document_id, "Processing failed", "Processing", "Needs Review",
                      "No readable text could be extracted.")
            return {"status": "review", "reason": "No readable text could be extracted."}

        predicted_type, confidence, probabilities = classify_document(text)
        fields = extract_fields(predicted_type, text)
        validation = validate_document(predicted_type, fields)
        decision = apply_rules(predicted_type, validation, confidence)

        elapsed = time.perf_counter() - started
        review_reason = decision["reason"] if decision["next_state"] == "Needs Review" else ""
        final_state = decision["next_state"]

        update_document_fields(
            document_id,
            document_type=predicted_type,
            company=fields.get("Company", ""),
            invoice_number=fields.get("Invoice Number", ""),
            total_amount=fields.get("Total Amount", ""),
            text_preview=text[:500],
            extracted_data=fields,
            predicted_confidence=confidence,
        )
        update_document_workflow(
            document_id,
            workflow_state=final_state,
            validation_errors=validation["errors"],
            review_reason=review_reason,
            last_action="Workflow decision",
            processing_time=elapsed,
            processing_error=0,
        )
        log_event(
            document_id,
            "Workflow decision",
            "Processing",
            final_state,
            decision["reason"],
        )
        return {
            "status": "processed" if final_state == "Completed" else "review",
            "reason": decision["reason"],
            "confidence": confidence,
            "document_type": predicted_type,
        }

    except Exception as exc:
        elapsed = time.perf_counter() - started
        update_document_workflow(
            document_id,
            workflow_state="Needs Review",
            validation_errors=[str(exc)],
            review_reason=f"Processing error: {exc}",
            last_action="Processing failed",
            processing_time=elapsed,
            processing_error=1,
        )
        log_event(document_id, "Processing failed", "Processing", "Needs Review", str(exc))
        return {"status": "failed", "reason": str(exc)}


def show_metrics():
    metrics = get_metrics()
    cols = st.columns(6)
    cols[0].metric("Total", metrics["total"])
    cols[1].metric("Completed", metrics["processed"])
    cols[2].metric("Needs Review", metrics["review"])
    cols[3].metric("Approved", metrics["approved"])
    cols[4].metric("Rejected", metrics["rejected"])
    cols[5].metric("Failed", metrics["failed"])

    st.subheader("Documents by Type")
    type_cols = st.columns(max(1, len(metrics["types"])))
    for index, (name, count) in enumerate(metrics["types"].items()):
        type_cols[index].metric(name, count)


def show_upload():
    st.header("📤 Upload & Workflow Processing")
    st.caption(
        "Workflow: Upload → Process → Classify → Extract → Validate → "
        "Apply Rules → Review/Approve/Reject → Complete → Audit"
    )

    uploaded_file = st.file_uploader(
        "Upload PDF, JPG, JPEG or PNG",
        type=["pdf", "jpg", "jpeg", "png"],
        key="week5_uploader",
    )
    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()
    file_hash = calculate_file_hash(file_bytes)
    existing = document_hash_exists(file_hash)

    if existing:
        st.warning("⚠️ Duplicate document detected.")
        st.write(f"**Existing ID:** {existing['id']}")
        st.write(f"**Filename:** {existing['original_filename']}")
        st.write(f"**Workflow State:** {existing['workflow_state']}")
        return

    if len(file_bytes) > 10 * 1024 * 1024:
        st.error("File is larger than the 10 MB upload limit.")
        return

    started = time.perf_counter()
    try:
        # Insert first so the workflow has a stable document ID and audit trail.
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        document_id = insert_document(
            original_filename=uploaded_file.name,
            stored_filename="",
            document_type="Other",
            upload_date=now,
            company="",
            invoice_number="",
            total_amount="",
            file_path="",
            text_preview="",
            file_hash=file_hash,
            status="New",
            workflow_state="New",
            last_action="Uploaded",
        )
        log_event(document_id, "Uploaded", None, "New", "Document uploaded.")

        transition_document(document_id, "Processing", "Processing started")

        storage_type = "other"
        lower_name = uploaded_file.name.lower()
        if "invoice" in lower_name:
            storage_type = "invoice"
        elif "resume" in lower_name or "cv" in lower_name:
            storage_type = "resume"

        storage_path = get_storage_path(storage_type, uploaded_file.name)
        with open(storage_path, "wb") as file:
            file.write(file_bytes)

        update_document_fields(
            document_id,
            text_preview="",
        )
        # Store path/filename using a direct DB update because these are storage metadata.
        from database import get_connection
        connection = get_connection()
        connection.execute(
            "UPDATE documents SET stored_filename=?, file_path=? WHERE id=?",
            (storage_path.name, str(storage_path), document_id),
        )
        connection.commit()
        connection.close()

        extracted_text = process_document(file_bytes, uploaded_file.name)
        if not extracted_text:
            elapsed = time.perf_counter() - started
            update_document_workflow(
                document_id,
                workflow_state="Needs Review",
                validation_errors=["No readable text could be extracted."],
                review_reason="No readable text could be extracted.",
                last_action="Processing failed",
                processing_time=elapsed,
                processing_error=1,
            )
            log_event(document_id, "Processing failed", "Processing", "Needs Review",
                      "No readable text could be extracted.")
            st.error("No readable text could be extracted. Document sent to review.")
            return

        predicted_type, confidence, probabilities = classify_document(extracted_text)
        fields = extract_fields(predicted_type, extracted_text)
        validation = validate_document(predicted_type, fields)
        decision = apply_rules(predicted_type, validation, confidence)
        elapsed = time.perf_counter() - started

        update_document_fields(
            document_id,
            document_type=predicted_type,
            company=fields.get("Company", ""),
            invoice_number=fields.get("Invoice Number", ""),
            total_amount=fields.get("Total Amount", ""),
            text_preview=extracted_text[:500],
            extracted_data=fields,
            predicted_confidence=confidence,
        )
        update_document_workflow(
            document_id,
            workflow_state=decision["next_state"],
            validation_errors=validation["errors"],
            review_reason=decision["reason"] if decision["next_state"] == "Needs Review" else "",
            last_action="Workflow decision",
            processing_time=elapsed,
            processing_error=0,
        )
        log_event(
            document_id,
            "Workflow decision",
            "Processing",
            decision["next_state"],
            decision["reason"],
        )

        st.success(f"Document saved successfully. ID: {document_id}")
        st.write(f"**Document Type:** {predicted_type}")
        if confidence is not None:
            st.write(f"**Classifier Confidence:** {confidence:.1%}")
        else:
            st.write("**Classifier Confidence:** Not available")
        st.write(f"**Workflow State:** {decision['next_state']}")
        st.write(f"**Reason:** {decision['reason']}")

        if validation["errors"]:
            st.warning("Validation results:")
            for error in validation["errors"]:
                st.write(f"- {error}")

        if fields:
            st.subheader("Extracted Fields")
            st.json(fields)

        if probabilities:
            st.subheader("Classification Probabilities")
            st.json(probabilities)

        with st.expander("Extracted Text"):
            st.text_area("Text", extracted_text, height=250, disabled=True)

    except Exception as exc:
        st.error(f"Document processing failed: {exc}")


def show_review_queue():
    st.header("🧑‍💼 Human Review Queue")
    documents = get_filtered_documents(workflow_state="Needs Review", sort_order="Newest")

    if not documents:
        st.success("No documents currently need review.")
        return

    st.info(f"{len(documents)} document(s) require human attention.")

    for document in documents:
        with st.container(border=True):
            st.subheader(f"#{document['id']} — {document['original_filename']}")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Type:** {document['document_type']}")
            col2.write(f"**State:** {document['workflow_state']}")
            col3.write(f"**Reason:** {document.get('review_reason') or 'Validation/review required'}")

            fields = parse_json(document.get("extracted_data"), {})
            errors = parse_json(document.get("validation_errors"), [])
            st.write("**Extracted Fields**")
            st.json(fields if fields else {"message": "No structured fields stored."})

            if errors:
                st.write("**Validation Failures**")
                for error in errors:
                    st.error(error)

            confidence = document.get("predicted_confidence")
            if confidence is not None:
                st.write(f"**Classifier confidence:** {confidence:.1%}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve", key=f"approve_{document['id']}"):
                    try:
                        transition_document(
                            document["id"], "Approved", "Reviewer approved",
                            "Reviewer approved the document."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with col_b:
                reject_reason = st.text_input(
                    "Rejection reason (required)",
                    key=f"reject_reason_{document['id']}",
                )
                if st.button("❌ Reject", key=f"reject_{document['id']}"):
                    try:
                        new_state, reason = review_decision(False, reject_reason)
                        transition_document(document["id"], new_state, "Reviewer rejected", reason)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            if document.get("workflow_state") == "Approved":
                if st.button("Complete Approved Document", key=f"complete_{document['id']}"):
                    try:
                        transition_document(
                            document["id"], "Completed", "Workflow completed",
                            "Approved document completed."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            history = get_audit_history(document["id"])
            with st.expander("Audit History"):
                st.dataframe(history, use_container_width=True)

    approved = get_filtered_documents(workflow_state="Approved", sort_order="Newest")
    if approved:
        st.subheader("✅ Approved Documents")
        st.caption("Approved documents can now be moved to Completed.")
        for document in approved:
            with st.container(border=True):
                st.write(f"**#{document['id']} — {document['original_filename']}**")
                st.write("Workflow State: **Approved**")
                if st.button("Complete", key=f"approved_complete_{document['id']}"):
                    try:
                        transition_document(
                            document["id"],
                            "Completed",
                            "Workflow completed",
                            "Approved document completed.",
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def show_batch():
    st.header("📦 Batch Workflow Processing")
    documents = get_filtered_documents(
        workflow_state="All",
        sort_order="Newest",
    )
    eligible = [
        d for d in documents
        if d["workflow_state"] in {"New", "Needs Review"}
    ]
    if not eligible:
        st.info("No New or Needs Review documents are available for batch processing.")
        return

    options = {
        f"#{d['id']} — {d['original_filename']} — {d['workflow_state']}": d["id"]
        for d in eligible
    }
    selected = st.multiselect("Select stored documents", list(options.keys()))

    if st.button("▶️ Run Workflow for Selected Documents", type="primary"):
        if not selected:
            st.warning("Select at least one document.")
            return

        processed = review = failed = 0
        results = []
        for label in selected:
            document_id = options[label]
            try:
                result = process_existing_document(document_id)
                if result["status"] == "processed":
                    processed += 1
                    outcome = "Completed"
                elif result["status"] == "review":
                    review += 1
                    outcome = "Needs Review"
                else:
                    failed += 1
                    outcome = "Failed → Needs Review"
                results.append({
                    "Document": label,
                    "Result": outcome,
                    "Reason": result["reason"],
                })
            except Exception as exc:
                failed += 1
                results.append({
                    "Document": label,
                    "Result": "Failed",
                    "Reason": str(exc),
                })

        st.success(
            f"Batch finished — Processed: {processed} | Review: {review} | Failed: {failed}"
        )
        st.dataframe(results, use_container_width=True)


def show_documents():
    st.header("🔎 Workflow Search & Filters")
    search = st.text_input("Search filename, type, company, invoice number or text")
    col1, col2, col3 = st.columns(3)
    with col1:
        state = st.selectbox(
            "Workflow State",
            ["All", "New", "Processing", "Needs Review", "Approved", "Rejected", "Completed"],
        )
    with col2:
        doc_type = st.selectbox("Document Type", ["All", "Invoice", "Resume", "Other"])
    with col3:
        sort = st.selectbox("Sort", ["Newest", "Oldest"])

    rows = get_filtered_documents(
        document_type=doc_type,
        workflow_state=state,
        sort_order=sort,
        search_text=search,
    )
    st.write(f"**{len(rows)} document(s)**")

    for document in rows:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**ID:** {document['id']}")
            col2.write(f"**File:** {document['original_filename']}")
            col3.write(f"**Type:** {document['document_type']}")
            col4.write(f"**State:** {document['workflow_state']}")
            st.write(
                f"**Latest action:** {document.get('last_action') or '-'} "
                f"at {document.get('last_action_at') or '-'}"
            )
            if document.get("review_reason"):
                st.warning(f"Review reason: {document['review_reason']}")
            with st.expander("Details"):
                st.write(f"**Company:** {document.get('company') or '-'}")
                st.write(f"**Invoice Number:** {document.get('invoice_number') or '-'}")
                st.write(f"**Total Amount:** {document.get('total_amount') or '-'}")
                confidence = document.get("predicted_confidence")
                st.write(
                    f"**Confidence:** {confidence:.1%}" if confidence is not None
                    else "**Confidence:** Not available"
                )
                fields = parse_json(document.get("extracted_data"), {})
                if fields:
                    st.json(fields)
                history = get_history(document["id"])
                if history:
                    st.dataframe(history, use_container_width=True)
                path = document.get("file_path")
                if path and os.path.exists(path):
                    with open(path, "rb") as file:
                        st.download_button(
                            "⬇️ Download",
                            data=file.read(),
                            file_name=document["original_filename"],
                            key=f"download_{document['id']}",
                        )


def show_dashboard():
    st.header("📊 Workflow Metrics Dashboard")
    show_metrics()
    st.subheader("Workflow States")
    rows = get_all_documents()
    if rows:
        state_counts = {}
        for row in rows:
            state = row["workflow_state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        st.dataframe(
            [{"Workflow State": state, "Count": count} for state, count in state_counts.items()],
            use_container_width=True,
        )
    else:
        st.info("No documents yet.")


def show_testing():
    st.header("🧪 Reliability & Failure Testing")
    st.write("Week 5 testing checklist:")
    checks = [
        "Normal invoice",
        "Normal resume",
        "Missing required fields",
        "Unreadable/scanned document",
        "Duplicate document",
        "Invalid email/date/amount",
        "Low-confidence classification when available",
        "Database/storage failure",
        "Invalid workflow transition",
        "Mixed-success batch processing",
    ]
    for item in checks:
        st.checkbox(item, key=f"test_{item}")

    st.subheader("Workflow Transition Test")
    if st.button("Run transition validation test"):
        invalid = not can_transition("Completed", "Processing")
        valid = can_transition("Needs Review", "Approved")
        if invalid and valid:
            st.success("Transition rules passed: invalid transition blocked and valid approval transition allowed.")
        else:
            st.error("Transition rule test failed.")


st.title("📄 AI Document Intelligence & Workflow Platform")
st.caption("ZYROO AI/ML Internship — Week 5: Advanced Document Workflow & Automation")

page = st.sidebar.radio(
    "Navigation",
    [
        "📤 Upload & Process",
        "🧑‍💼 Review Queue",
        "📦 Batch Processing",
        "🔎 Search & Filters",
        "📊 Metrics Dashboard",
        "🧪 Reliability Testing",
    ],
)

if page == "📤 Upload & Process":
    show_upload()
elif page == "🧑‍💼 Review Queue":
    show_review_queue()
elif page == "📦 Batch Processing":
    show_batch()
elif page == "🔎 Search & Filters":
    show_documents()
elif page == "📊 Metrics Dashboard":
    show_dashboard()
else:
    show_testing()
