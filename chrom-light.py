import classes.models as models
import classes.states as states
import classes.data_handle as dh
import numpy as np
import logging
import argparse
import os
__version__ = '0.0.2'


if __name__ == '__main__':
    # #############################################
    # #############################################
    # ARGUMENT PARSER
    parser = argparse.ArgumentParser(description='Chrom')
    parser.add_argument('-i', '--input', nargs='+', action='store', dest='filename', type=str, required=True,
                        help='Bam or tsv files containing reads from ATACseq experiment (Required)')
    parser.add_argument('-sb', '--saveBedFile', action='store', dest='save_bed', type=str, required=True,
                        default=None, help='save bedfile. Input path to save (default is False).')
    parser.add_argument('-reg', '--regions', action='store', dest='regions', type=bool, required=False,
                        default=False, help='Parse reads on selected regions (Optional)')
    parser.add_argument('-it', '--iterations', action='store', dest='iterations', type=int, required=False,
                        default=20, help='Number of iterations to fit the algorithm (default = 10, optional)')

    parser.add_argument('-spec', '--species', action='store', dest='species', type=str, required=False,
                        default='mouse', help='Genome Species mouse, human (default = mouse, optional)')
    parser.add_argument('-sc', '--single_chrom', action='store', dest='single_chrom', type=int, required=False,
                        default=None, help='Process a single chromosome (default = None, optional)')
    parser.add_argument('-inf', '--inference', action='store', dest='inference', type=str, required=False,
                        default='batch', help='Inference algorithm: batch, mo, so (default = Batch, optional)')
    parser.add_argument('-sen', '--sensitivity', action='store', dest='sensitivity', type=str, required=False,
                        default="high", help='Sensitivity high or low(default is high).')
    parser.add_argument('-bl', '--blacklisted', action='store', dest='blacklisted', type=bool, required=False,
                        default=True, help='Remove Blacklisted peaks. (default is True).')

    parser.add_argument('-nome', '--no-metrics', action='store', dest='no_metrics', type=bool, required=False,
                        default=False, help='Flag to Compute Metrics. (default is True).')
    parser.add_argument('-sp', '--savePickleFile', action='store', dest='save_pickle', type=str, required=False,
                        default=None, help='save pickle file (default is False)')
    parser.add_argument('-ve', '--verbose', action='store', dest='verbose_level', type=str, required=False,
                        default='1', help='verbose level. 1 display messages, 0 omit them (default is 0).')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    options = parser.parse_args()
    # #############################################
    # #############################################

    # #############################################
    # #############################################
    # BUILDING LOGGER
    if options.save_bed is not None:
        name = options.save_bed + '.log'
    else:
        name = None
    dh.build_logger(options.verbose_level, filename=name)
    logger = logging.getLogger()

    # VALIDATE INPUTS
    dh.validate_inputs(options.filename)
    # #############################################
    # #############################################

    # #############################################
    # #############################################
    # BUILDING PARAMETERS SINGLE EXPERIMENT
    for _ in np.arange(len(options.filename)):
        logger.info("Processing File:{}".format(options.filename[_]))

    if options.sensitivity == "auto":
        pi_prior, tmat_prior, state_list, top_states = models.auto(file=options.filename, spec=options.species)
    else:
        pi_prior, tmat_prior, state_list, top_states = states.build_states(typ=options.sensitivity,
                                                                           filename=options.filename)

    # #############################################
    # #############################################

    # #############################################
    # #############################################
    # CREATE MODEL AND FIT
    hsmm = models.BayesianHsmmExperimentMultiProcessing(states=state_list, top_states=top_states,
                                                        compute_regions=options.regions,
                                                        pi_prior=pi_prior, tmat_prior=tmat_prior,
                                                        blacklisted=options.blacklisted)
    hsmm.train(filename=options.filename, species=options.species, single_chr=options.single_chrom,
               iterations=options.iterations, opt=options.inference)
    # #############################################
    # #############################################

    # #############################################
    # #############################################
    # SAVING INTO BEDFILE OR PICKLE
    if options.save_bed is not None:
        logger.info("Saving Bed File")
        path, filename = os.path.split(options.save_bed)
        hsmm.save_bedfile(path=path, name=filename)
        # hsmm.save_bedfile_individual_states(path=path, name=filename, t_range=True)
        if not options.no_metrics:
            dh.metrics(filename=options.filename, annotations=hsmm.peaks, species=options.species)

    if options.save_pickle is not None:
        logger.info("Saving Data Object File")
        path, filename = os.path.split(options.save_pickle + '.pkl')
        hsmm.save_statevariables(path=path, name=filename + 'state')
        hsmm.save_dataobject(path=path, name=filename)
    # #############################################
    # #############################################
