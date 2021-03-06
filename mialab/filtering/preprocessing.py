"""Enables the enhancement of images before their use with other algorithms."""
import SimpleITK as sitk
import numpy as np

import mialab.filtering.filter as fltr
import pickle
from medpy.filter import IntensityRangeStandardization



class BiasFieldCorrectorParams(fltr.IFilterParams):
    """Bias field correction filter parameters."""

    def __init__(self, mask: sitk.Image):
        """Initializes a new instance of the BiasFieldCorrectorParams class.

        Args:
            mask (sitk.Image): A mask image (0=background; 1=mask).

        Examples:
            To generate a default mask use Otsu's thresholding:

            >>> sitk.OtsuThreshold( image, 0, 1, 200 )
        """
        self.mask = mask


class BiasFieldCorrector(fltr.IFilter):
    """Represents a bias field correction filter."""

    def __init__(self, shrink_factor=1, convergence_threshold=0.001, max_iterations=(50, 50, 50, 50),
                 fullwidth_at_halfmax = 0.15, fiter_noise=0.01, histogram_bins=200, control_points=(4,4,4),
                 spline_order=3):
        """Initializes a new instance of the BiasFieldCorrector class.

        Args:
            shrink_factor (float): The shrink factor. A higher factor decreases the computational time.
            convergence_threshold (float): The threshold to stop the optimizer.
            max_iterations (list of int): The maximum number of optimizer iterations at each level.
            fullwidth_at_halfmax (float): ?
            fiter_noise (float): Wiener filter noise.
            histogram_bins (int): Number of histogram bins.
            control_points (list of int): The number of spline control points.
            spline_order (int): The spline order.
        """
        super().__init__()
        self.shrink_factor = shrink_factor
        self.convergence_threshold = convergence_threshold
        self.max_iterations = max_iterations
        self.fullwidth_at_halfmax = fullwidth_at_halfmax
        self.filter_noise = fiter_noise
        self.histogram_bins = histogram_bins
        self.control_points = control_points
        self.spline_order = spline_order

    def execute(self, image: sitk.Image, params: BiasFieldCorrectorParams=None) -> sitk.Image:
        """Executes a bias field correction on an image.

        Args:
            image (sitk.Image): The image.
            params (BiasFieldCorrectorParams): The bias field correction filter parameters.

        Returns:
            sitk.Image: The bias field corrected image.
        """

        mask = params.mask if params is not None else sitk.OtsuThreshold(image, 0, 1, 200)
        if self.shrink_factor > 1:
            raise ValueError('shrinking is not supported yet')
        return sitk.N4BiasFieldCorrection(image, mask, self.convergence_threshold, self.max_iterations,
                                          self.fullwidth_at_halfmax, self.filter_noise, self.histogram_bins,
                                          self.control_points, self.spline_order)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'BiasFieldCorrector:\n' \
               ' shrink_factor:         {self.shrink_factor}\n' \
               ' convergence_threshold: {self.convergence_threshold}\n' \
               ' max_iterations:        {self.max_iterations}\n' \
               ' fullwidth_at_halfmax:  {self.fullwidth_at_halfmax}\n' \
               ' filter_noise:          {self.filter_noise}\n' \
               ' histogram_bins:        {self.histogram_bins}\n' \
               ' control_points:        {self.control_points}\n' \
               ' spline_order:          {self.spline_order}\n' \
            .format(self=self)


class GradientAnisotropicDiffusion(fltr.IFilter):
    """Represents a gradient anisotropic diffusion filter."""

    def __init__(self,
                 time_step: float=0.125,
                 conductance: int=3,
                 conductance_scaling_update_interval: int=1,
                 no_iterations: int=5):
        """Initializes a new instance of the GradientAnisotropicDiffusion class.

        Args:
            time_step (float): The time step.
            conductance (int): The conductance (the higher the smoother the edges).
            conductance_scaling_update_interval: TODO
            no_iterations (int): Number of iterations.
        """
        super().__init__()
        self.time_step = time_step
        self.conductance = conductance
        self.conductance_scaling_update_interval = conductance_scaling_update_interval
        self.no_iterations = no_iterations

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:
        """Executes a gradient anisotropic diffusion on an image.

        Args:
            image (sitk.Image): The image.
            params (fltr.IFilterParams): The parameters (unused).

        Returns:
            sitk.Image: The smoothed image.
        """
        return sitk.GradientAnisotropicDiffusion(sitk.Cast(image, sitk.sitkFloat32),
                                                 self.time_step,
                                                 self.conductance,
                                                 self.conductance_scaling_update_interval,
                                                 self.no_iterations)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'GradientAnisotropicDiffusion:\n' \
               ' time_step:                           {self.time_step}\n' \
               ' conductance:                         {self.conductance}\n' \
               ' conductance_scaling_update_interval: {self.conductance_scaling_update_interval}\n' \
               ' no_iterations:                       {self.no_iterations}\n' \
            .format(self=self)


class NormalizeZScore(fltr.IFilter):
    """Represents a z-score normalization filter."""

    def __init__(self):
        """Initializes a new instance of the NormalizeZScore class."""
        super().__init__()

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:
        """Executes a z-score normalization on an image.

        Args:
            image (sitk.Image): The image.
            params (fltr.IFilterParams): The parameters (unused).

        Returns:
            sitk.Image: The normalized image.
        """

        img_arr = sitk.GetArrayFromImage(image)

        mean = img_arr.mean()
        std = img_arr.std()
        img_arr = (img_arr - mean) / std

        img_out = sitk.GetImageFromArray(img_arr.astype(np.float32))
        img_out.CopyInformation(image)

        return img_out

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'NormalizeZScore:\n' \
            .format(self=self)


class Gaussian(fltr.IFilter):
    """Represents a gaussian filter."""

    def __init__(self,
                 sigma: int=1):
        """Initializes a new instance of the Gaussian class."""
        super().__init__()
        self.sigma = sigma

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:

        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(self.sigma)

        return gaussian.Execute(image)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'Gaussian:\n' \
            .format(self=self)


class Median(fltr.IFilter):
    """Represents a median filter."""

    def __init__(self,
                 radius: int=1):
        """Initializes a new instance of the Median class."""
        super().__init__()
        self.radius = radius

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:

        median = sitk.MedianImageFilter()
        median.SetRadius(self.radius)

        return median.Execute(image)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'Median:\n' \
            .format(self=self)


class RescaleIntensity(fltr.IFilter):
    """Represents a rescale intensity filter."""

    def __init__(self, min_intensity, max_intensity):
        """Initializes a new instance of the RescaleIntensity class.

        Args:
            min_intensity (int): The min intensity value.
            max_intensity (int): The max intensity value.
        """
        super().__init__()
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:
        """Executes an intensity rescaling on an image.

        Args:
            image (sitk.Image): The image.
            params (fltr.IFilterParams): The parameters (unused).

        Returns:
            sitk.Image: The intensity rescaled image.
        """

        return sitk.RescaleIntensity(image, self.min_intensity, self.max_intensity)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'RescaleIntensity:\n' \
               ' min_intensity: {self.min_intensity}\n' \
               ' max_intensity: {self.max_intensity}\n' \
            .format(self=self)


class HistogramMatcherParams(fltr.IFilterParams):
    """Histogram matching filter parameters."""

    def __init__(self, reference_image: sitk.Image):
        """Initializes a new instance of the HistogramMatcherParams class.

        Args:
            reference_image (sitk.Image): Reference image for the matching.
        """
        self.reference_image = reference_image


class HistogramMatcher(fltr.IFilter):
    """A method to align the intensity ranges of images."""

    def __init__(self, histogram_levels=256, match_points=1, threshold_mean_intensity=True):
        """Initializes a new instance of the HistogramMatcher class.

        Args:
            histogram_levels (int): Number of histogram levels.
            match_points (int): Number of match points.
            threshold_mean_intensity (bool): Threshold at mean intensity.
        """
        super().__init__()
        self.histogram_levels = histogram_levels
        self.match_points = match_points
        self.threshold_mean_intensity = threshold_mean_intensity

    def execute(self, image: sitk.Image, params: HistogramMatcherParams = None) -> sitk.Image:
        """Matches the image intensity histogram to a reference.

        Args:
            image (sitk.Image): The image.
            params (HistogramMatcherParams): The parameters.

        Returns:
            sitk.Image: The filtered image.
        """
        if params is None:
            raise ValueError('Parameter with reference image is required')

        return sitk.HistogramMatching(image, params.reference_image, self.histogram_levels, self.match_points,
                                      self.threshold_mean_intensity)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'HistogramMatcher:\n' \
               ' histogram_levels:         {self.histogram_levels}\n' \
               ' match_points:             {self.match_points}\n' \
               ' threshold_mean_intensity: {self.threshold_mean_intensity}\n' \
            .format(self=self)


class IRS(fltr.IFilter):
    """Represents a intensity range standardization filter implemented with Medpy."""

    def __init__(self, model_path='bin/mia-model/hmmModel.pkl', train=False):
        """Initializes a new instance of the HistMatcher class."""
        super().__init__()
        self.model_path = model_path
        self.train = train

        if self.train:
            self.train_images = []
            self.irs = IntensityRangeStandardization()
        else:
            with open(model_path, 'r') as f:
                self.irs = pickle.load(f)

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:
        img_array = sitk.GetArrayFromImage(image)
        if self.train:
            self.train_images.append(img_array)
            self.irs.train(self.train_images)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.irs, f)
            return image
        else:
            return sitk.Image(self.irs.transform(img_array), sitk.sitkUInt8)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'IRS:\n' \
               ' model_path:         {self.model_path}\n' \
               ' train:             {self.train}\n' \
            .format(self=self)


class Bilateral(fltr.IFilter):
    """Represents a bilateral filter."""

    def __init__(self, domainSigma=4.0, rangeSigma=50.0):
        """Initializes a new instance of the bilateral class."""
        super().__init__()
        self.domainSigma = domainSigma
        self.rangeSigma = rangeSigma

    def execute(self, image: sitk.Image, params: fltr.IFilterParams=None) -> sitk.Image:
        return sitk.Bilateral(image, domainSigma=self.domainSigma, rangeSigma=self.rangeSigma)

    def __str__(self):
        """Gets a printable string representation.

        Returns:
            str: String representation.
        """
        return 'Bilateral:\n' \
               ' domainSigma:         {self.domainSigma}\n' \
               ' rangeSigma:             {self.rangeSigma}\n' \
            .format(self=self)
