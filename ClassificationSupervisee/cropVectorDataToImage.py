# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISEducation
                                 A QGIS plugin
 QGISEducation
                              -------------------
        begin               : 2016-06-02
        copyright           : (C) 2016 by CNES
        email               : alexia.mondot@c-s.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# import system libraries
import argparse
import glob
import os
import sys
import shutil

from TerreImage.terre_image_gdal_api import get_image_epsg_code_with_gdal, get_vector_epsg_with_ogr

# import logging for debug messages
import logging
logging.basicConfig()
# create logger
logger = logging.getLogger('cropVectorDataToImage')
logger.setLevel(logging.DEBUG)


def usage(argParser, return_code = 1):
    """
    Usage
    :param argParser:
    :param return_code:
    :return:
    """
    print argParser.format_usage()
    sys.exit(return_code)


def get_arguments():
    """
    Manages inputs
    :return:
    """

    # check inputs
    logger.info("######## MANAGING ARGUMENTS ########")
    logger.debug("Checking arguments")

    argParser = argparse.ArgumentParser()
    required_arguments = argParser.add_argument_group('required arguments')
    required_arguments.add_argument('-v', '--inputVectorFileName', required=True,
                                    help='Path to the input vector ex: road.shp')
    required_arguments.add_argument('-i', '--inputImageFileName', required=True,
                                    help='Path to input image')
    required_arguments.add_argument('-o', '--output_directory', required=True,
                                    help='Path to output directory')

    logger.debug(len(sys.argv))
    if len(sys.argv) != 11:
        usage(argParser)

    args = argParser.parse_args(sys.argv[1:])
    input_vector = args.inputVectorFileName
    input_image = os.path.realpath(args.inputImageFileName)
    output_directory = os.path.realpath(args.output_directory)

    logger.debug("Arguments ok")

    # crating directories if they don't exist
    logger.debug("Managing output directories")
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    logger.debug("Output directories ok")


    # checking if inputs exist
    if not os.path.isfile(input_image):
        print "Error, input image is missing "
        usage(argParser, 2)
    if not os.path.isfile(input_vector):
        print "Error, input vector is missing "
        usage(argParser, 2)

    return input_image, input_vector, output_directory



def GenerateEnvelope(inputImageFileName, output_directory):
    """
    Computes the envelope of the given image
    Args:
        inputImageFileName:
        outputImageEnvelopeVector:

    Returns:

    """
    outputImageEnvelopeVector = os.path.join(output_directory, "image_envelope.shp")
    command = "otbcli_ImageEnvelope -in {} -out {}".format(inputImageFileName, outputImageEnvelopeVector)
    os.system(command)
    return outputImageEnvelopeVector


def ReprojectVector(inputVectorFileName,  inputImageFileName, output_directory):
    """
    Reprojects the given vector in the coordinate system of the given image
    Args:
        inputVectorFileName:
        inputImageFileName:
        tmpReprojectedVector:

    Returns:

    """
    epsg_code = get_image_epsg_code_with_gdal(inputImageFileName)

    # use of .qpj instead of incomplete .prj
    if os.path.isfile(os.path.splitext(inputVectorFileName)[0] + ".qpj"):
        shutil.copy(os.path.splitext(inputVectorFileName)[0] + ".qpj", os.path.splitext(inputVectorFileName)[0] + ".prj")
    # test authority code availability
    epsg_vector = get_vector_epsg_with_ogr(inputVectorFileName)
    if not epsg_vector:
        print "Bad projection !"
        #raise
        # TODO add exception

    tmpReprojectedVector = os.path.join(output_directory, "tmp_reprojected.shp")
    # command = "otbcli_VectorDataReprojection -in.vd {} -out.proj.image.in {} -out.vd {}".format(inputVectorFileName,
    #                                                                                             inputImageFileName,
    #                                                                                             tmpReprojectedVector)
    #command = "ogr2ogr -t_srs {} -s_srs {} {} {}".format(epsg_code, None, tmpReprojectedVector, inputVectorFileName)
    command = "ogr2ogr -t_srs EPSG:{} {} {}".format(epsg_code, tmpReprojectedVector, inputVectorFileName)

    os.system(command)
    return tmpReprojectedVector


def IntersectLayers(tmpReprojectedVector, outputImageEnvelopeVector, output_directory):
    """
    Produces the intersection between tmpReprojectedVector and outputImageEnvelopeVector
    Args:
        tmpReprojectedVector:
        outputImageEnvelopeVector:
        outputVectorFileName:

    Returns:

    """
    outputVectorFileName = os.path.join(output_directory, "preprocessed.shp")
    commandOGR = "ogr2ogr -f 'ESRI Shapefile' -clipsrc {} {} {}".format(outputImageEnvelopeVector,
                                                                        outputVectorFileName,
                                                                        tmpReprojectedVector)
    os.system( commandOGR )
    return outputVectorFileName


def cropVectorDataToImage(inputImageFileName, inputVectorFileName, output_directory):
      # const char* tmpReprojectedVector = argv[4];
      # const char* outputVectorFileName = argv[5];

    # Generate a shp file with image envelope
    # CRS is the image CRS
    outputImageEnvelopeVector = GenerateEnvelope(inputImageFileName, output_directory)


    # Reproject input vector into image CRS
    tmpReprojectedVector = ReprojectVector(inputVectorFileName,  inputImageFileName, output_directory)


    # Generate intersection between reprojected input vector and image envelope
    outputVectorFileName = IntersectLayers(tmpReprojectedVector, outputImageEnvelopeVector, output_directory)

    return outputVectorFileName


if __name__ == '__main__':
    input_image, input_vector, output_directory = get_arguments()
    cropVectorDataToImage(input_image, input_vector, output_directory)
