from secureli.modules.shared.models.scan import ScanFailure, ScanResult


def merge_scan_results(results: list[ScanResult]):
    """
    Creates a single ScanResult from multiple ScanResults
    :param results: The list of ScanResults to merge
    :return A single ScanResult
    """
    final_successful = True
    final_output = ""
    final_failures: list[ScanFailure] = []

    for result in results:
        if result:
            final_successful = final_successful and result.successful
            final_output = final_output + (result.output or "") + "\n"
            final_failures = final_failures + result.failures

    return ScanResult(
        successful=final_successful, output=final_output, failures=final_failures
    )
