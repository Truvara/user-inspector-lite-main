import logging
from pathlib import Path
from parser import DataParser
from inspector import AccessInspector
from reporter import AccessReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize paths
        data_folder = Path('data')

        logger.info("Starting access review process...")

        # Parse data
        logger.info("Parsing input data...")
        parser = DataParser(data_folder)
        parsed_dfs = parser.load_and_parse()
        logger.info("Data parsing completed")

        # Perform compliance checks
        logger.info("Running compliance checks...")
        inspector = AccessInspector(parsed_dfs)
        
        inspection_results = {
            'joiner_checks': inspector.joiner_checks(),
            'leaver_checks': inspector.leaver_checks(),
            'idle_checks': inspector.idle_checks(),
            'system_user_checks': inspector.system_user_checks()
        }
        
        # Generate summaries
        summaries = inspector.generate_summaries()
        inspection_results.update(summaries)  # Add summaries to results
        
        logger.info("Compliance checks completed")

        # Generate reports
        logger.info("Generating reports...")
        reporter = AccessReporter(parsed_dfs, inspection_results)
        report_path = reporter.generate_full_report()
        
        logger.info(f"Access review completed. Report saved at: {report_path}")

        logger.info("Access review process completed successfully")

    except Exception as e:
        logger.error(f"Error in access review process: {str(e)}")
        raise

if __name__ == "__main__":
    main()