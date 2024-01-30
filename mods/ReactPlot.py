import matplotlib.pyplot as plt
import matplotlib as mpl
from mods.common_functions import is_number, random_color

import numpy as np


class PlotStuff:
    def __init__(self, react_style=True):
        # Use standard white background insted of REACT color scheme?
        self.react_style = react_style

        # Init matplotlib.pyplot settings
        self.set_plot_settings(self.react_style)

        # Make plot pop up relative to REACT main window:
        mpl.use("Qt5agg")

        # With Qt5agg we need to turn the interactive mode on!
        plt.ion()

    def set_figure_save_settings(self):
        pass

    def set_plot_settings(self, react_style=True):
        """
        Defines mpl.rcParams
        :return:
        """

        # REACT color scheme:
        react_white = "#dcdcdc"
        react_blue = "#6272a4"
        react_pink = "#8f1777"
        react_bg_dark = "#141414"
        react_bg = "#1e1e1e"

        if not react_style:
            react_white = "#141414" # dark now --> darker: "#1e1e1e"
            react_blue = "#1e1e1e"
            react_pink = "#1e1e1e"
            react_bg_dark ="#FFFFFF" # white now
            react_bg = "#FFFFFF"


        # Size of window = 700 x 500 px
        mpl.rcParams["figure.figsize"] = (7, 5)
        mpl.rcParams["figure.dpi"] = 100

        # Save figure options (high resolution eps, with transparent background)
        mpl.rcParams["savefig.dpi"] = 300
        mpl.rcParams["savefig.format"] = "eps"  # {png, ps, pdf, svg}
        mpl.rcParams["savefig.transparent"] = True

        # General settings
        mpl.rcParams["xtick.color"] = react_white
        mpl.rcParams["ytick.color"] = react_white

        # Main figure frame
        mpl.rcParams["figure.facecolor"] = react_bg_dark
        mpl.rcParams["figure.edgecolor"] = react_blue

        mpl.rcParams["figure.autolayout"] = True

        # Layout
        mpl.rcParams["figure.subplot.top"] = 0.88
        mpl.rcParams["figure.subplot.wspace"] = 0.70
        mpl.rcParams["figure.subplot.hspace"] = 0.35
        mpl.rcParams["figure.subplot.right"] = 0.96

        # Subplots
        mpl.rcParams["axes.facecolor"] = react_bg
        mpl.rcParams["axes.titlecolor"] = react_pink
        mpl.rcParams["axes.edgecolor"] = react_blue
        mpl.rcParams["axes.labelcolor"] = react_white
        mpl.rcParams["text.color"] = react_blue
        mpl.rcParams["axes.titleweight"] = "bold"

        # Subplot legends
        mpl.rcParams["legend.framealpha"] = 0

        mpl.rcParams["axes.formatter.useoffset"] = False

        custom_colors = ['8f1777', '1f77b4', 'ff7f0e', '2ca02c', 'd62728',
                                                       '9467bd', '8c564b', 'e377c2', '7f7f7f', 'bcbd22', '17becf']
        #Add 100 more colors:
        for i in range(100):
            custom_colors.append(random_color())

        mpl.rcParams["axes.prop_cycle"] = mpl.cycler('color', custom_colors )

    def set_axes_font_size(self, size=12):
        mpl.rc('axes', titlesize=size)

    def set_axes_label_size(self, size=12):
        mpl.rc('axes', labelsize=size)
        mpl.rcParams['axes.labelsize'] = size

    def set_xtick_label_size(self, size=12):
        mpl.rc('xtick', labelsize=size)

    def set_ytick_label_size(self, size=12):
        mpl.rc('ytick', labelsize=size)

    def set_legend_size(self, size=12):
        mpl.rc('legend', fontsize=size)

    def set_figure_title_size(self, size=12):
        mpl.rc('figure', titlesize=size)

    def update_style(self, fig, ax, title=None):
        """
        Required for real-time updating of style
        :return:
        """
        fig.set_edgecolor(mpl.rcParams["figure.edgecolor"])
        fig.set_facecolor(mpl.rcParams["figure.facecolor"])

        ax.set_facecolor(mpl.rcParams["axes.facecolor"])

        # Clumsy way to set axes edge color:
        for where in ["bottom", "top", "right", "left"]:
            ax.spines[where].set_color(mpl.rcParams["axes.edgecolor"])

        for where in ["x", "y"]:
            ax.tick_params(axis=where, colors=mpl.rcParams["xtick.color"])

        ax.yaxis.label.set_color(mpl.rcParams["axes.labelcolor"])
        ax.xaxis.label.set_color(mpl.rcParams["axes.labelcolor"])
        ax.xaxis.label.set_size(mpl.rcParams["axes.labelsize"])
        ax.yaxis.label.set_size(mpl.rcParams["axes.labelsize"])



        # Don't mess with title color unless there is a title - it will display color code in title then
        if title:
            ax.set_title(color=mpl.rcParams["axes.titlecolor"])


class SinglePlot(PlotStuff):
    def __init__(self, x_data, y_data, x_title=None, y_title=None, plot_title=None):
        super().__init__()

        self.x_data = x_data
        self.x_title = x_title

        self.y_data = y_data
        self.y_title = y_title

        self.plot_title = plot_title

        self.make_plot()

    def make_plot(self):
        """

        :return:
        """
        fig = plt.figure()
        plot = fig.add_subplot(1, 1, 1)
        if self.plot_title:
            plot.set_title(self.plot_title)
        if self.y_title:
            plot.set_ylabel(self.y_title)
        if self.x_title:
            plot.set_xlabel(self.x_title)

        plot.plot(self.x_data, self.y_data)
        plt.show()


class SpectrumIR(SinglePlot):
    """
    The IR intensity I(IR) predicted by Gaussian is based on the napierian absorbance, Ae = ln(I0/I), and is printed in
    units of (km mol–1) = (1000 m mol–1). To obtain the band area A based on the linear absorbance A = log10(I0/I) and
    in units of (1000 cm mol–1) the intensity I(IR) must be divided by ln10 and multiplied by 100:
    A = 100/ln10 ∙ I(IR) = 43.42945 ∙ I(IR).
    """
    def __init__(self, x_data, y_data, x_title=None, y_title=None, plot_title=None):
        self.wavenrs, self.eps_nrs = self.make_multi_lorentzian(x_data, y_data)

        # Normalise intensities
        self.eps_nrs = [x / max(self.eps_nrs) for x in self.eps_nrs]

        super().__init__(self.wavenrs, self.eps_nrs, x_title="Frequency", y_title="Intensity")

    def lorentzian(self, ir, v, v0, w=20.):
        """
        eps(v) = (2A / pi) * (w / (4(v - v0)**2))
            eps = molar absorption coefficient (L mol-1 cm-1) = (1000 cm2 mol-1)
            A = area (L mol-1 cm-1 x cm-1) = (1000 cm mol-1)
            v = wavenumber (cm-1)
            v0 = Wavenumber at band center (cm-1)

        The IR intensity I(IR) predicted by Gaussian is based on the napierian absorbance, Ae = ln(I0/I), and is printed
        in units of (km mol–1) = (1000 m mol–1). To obtain the band area A based on the linear absorbance
        A = log10(I0/I) and in units of (1000 cm mol–1) the intensity I(IR) must be divided by ln10 and
        multiplied by 100: A = 100/ln10 ∙ I(IR) = 43.42945 ∙ I(IR).
            --> (2A / pi) = 2 * 43.42945 * I(IR) / pi = 27.64804 * I(IR)

        :param ir: IR intensity at band center
        :param v: wavenumber (cm-1)
        :param v0: Wavenumber at band center (cm-1)
        :param w: full width at half height (cm-1)

        :return: IR intensity at wavenumber, w (cm-1)
        """

        return 27.64804 * ir * (w / (4. * (v - v0) ** 2 + w ** 2))

    def make_lorentzian_lineshape(self, v0, intensity, v_start, v_end, w=20):
        """

        Generates Lorentzian line-shape around wavenumber v0 with max intensity, intensity, starting from wavenumber
        v_start up until wavenumber v_end.

        :param v0: Wavenumber at band center (cm-1)
        :param intensity: IR intensity at band center
        :param v_start:
        :param v_end:
        :param w: full width at half height (cm-1)

        :return: wavenumbers (list) and corresponding intensites (list)
        """
        wavenumbers = list()
        intensities = list()

        for v in range(v_start, v_end):
            wavenumbers.append(v)
            intensities.append(self.lorentzian(intensity, v, v0, w))

        return wavenumbers, intensities

    def make_multi_lorentzian(self, wavenumbers, intensities, w=20):
        """

        Combines several Lorentzian curves by adding overlaps to a IR spectrum-like continuous line-shape.

        :param wavenumbers: Wavenumbers/frequencies from Gaussian frequency calculations
        :param intensities: Intensities from Gaussian frequency calculations
        :param w: full width at half height (cm-1)

        :return: wavenumbers and amplitudes/intensities fitted to Lorentzian
        """
        wavenr_freq = dict()
        start = 0
        end = int(max(wavenumbers)) + 500

        for i in range(len(wavenumbers)):

            intensity = intensities[i]
            v0 = wavenumbers[i]

            w_nrs, f = self.make_lorentzian_lineshape(v0, intensity, start, end, w)

            # add Lorentzian wavenumber and intensities to additive multi-Lorentzian:
            for j in range(len(w_nrs)):
                if w_nrs[j] not in wavenr_freq.keys():
                    wavenr_freq[w_nrs[j]] = f[j]
                else:
                    wavenr_freq[w_nrs[j]] += f[j]

        w_nrs, amplitudes = zip(*sorted(wavenr_freq.items()))

        return w_nrs, amplitudes


class PlotEnergyDiagram(PlotStuff):
    def __init__(self, ene_array, parent=None, legends=None, x_title=None, y_title=None, plot_title=None,
                 plot_legend=False, line_colors=None, react_style=True, custom_names=None, activation=None, reaction=None):
        self.x_title = x_title
        self.y_title = y_title
        self.plot_title = plot_title
        self.plot_legend = plot_legend
        self.legends = legends
        self.line_colors = line_colors
        self.parent = parent
        self.custom_names = custom_names
        self.activation = activation
        self.reaction = reaction

        super().__init__(react_style=react_style)

        # create figure and axis:
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.mpl_connect('close_event', self.close)

        self.ene_array = self.check_array(ene_array)

        if not self.parent:
            self.plot_energy_diagram(self.ene_array)

    def close(self, event):
        if self.parent:
            self.parent.plot = None
            plt.close()

    def check_array(self, ene_array):
        """
        Check if ene_array is list of lists. if not, make it so
        :param ene_array:
        :return: ene_array
        """
        if not any(isinstance(x, list) for x in ene_array):
            ene_array = [ene_array]

        return ene_array

    def energy_rank(self, energies, marker_width=.5, color='r'):
        """
        Takes a list of Y-values and returns lines for energy diagram
        :param energies: array of Y-data (energies)
        :param marker_width:
        :return: energy diagram lines
        """
        y_data = np.repeat(energies, 2)
        x_data = np.empty_like(y_data)

        x_data[0::2] = np.arange(1, len(energies) + 1) - (marker_width/2)
        x_data[1::2] = np.arange(1, len(energies) + 1) + (marker_width/2)
        lines = list()

        # Remove None values while keeping correct x-positions (allows for jumps in energy diagram):
        for i in range(len(y_data) - 1, -1, -1):
            if y_data[i] is None:
                y_data = np.delete(y_data, i)
                x_data = np.delete(x_data, i)

        lines.append(plt.Line2D(x_data, y_data, lw=1, linestyle="dashed", color=color))

        for x in range(0, len(energies)*2, 2):
            if is_number(x):
                lines.append(plt.Line2D(x_data[x:x+2], y_data[x:x+2], lw=4, linestyle="solid", color=color))

        return lines

    def get_bounds(self, ene_array):
        """

        :return:
        """
        x_min = 0.5
        x_max = 0
        y_min = 0
        y_max = 0

        for plot in ene_array:
            if len(plot) > x_max:
                x_max = len(plot)
            for ene in plot:
                if is_number(ene):
                    if ene > y_max:
                        y_max = ene
                    if ene < y_min:
                        y_min = ene

        return x_min, x_max + 0.5, y_min - 1, y_max + 1

    def make_energy_diagram(self, ene_array):
        """
        Takes array and creates connected Line2D energy diagram
        :param ene_array: [ [energies_plot1], [energies_plot2],...]
        :return: plots: Line2D
        :return: legend_elements: labels for each connected Line2D (energy diagram)
        """
        # Collect artists Line2D:
        plots = list()

        # Custom legends:
        legend_elements = list()

        # Make energy diagrams:
        for i in range(len(ene_array)):
            # Need to manually assign colors for this type of Line2D plot:
            color = plt.rcParams['axes.prop_cycle'].by_key()['color'][i]

            if self.line_colors:
                color = self.line_colors[i]

            # Label lines:
            label = str(i+1)
            if self.legends:
                label = self.legends[i]

            legend_elements.append(plt.Line2D([0], [0], color=color, lw=3, label=label))
            plots.append(self.energy_rank(energies=ene_array[i], marker_width=.5, color=color))

            # Find the maximum y-value and its corresponding x-value
            try:

                # Make energy diagrams:
                for i in range(len(ene_array)):

                    # Get the energy rank lines for the current set of energies
                    #energy_lines = self.energy_rank(energies=ene_array[i], marker_width=.5, color=color)

                    # Add the energy lines to the plot
                    #for line in energy_lines:
                    #    self.ax.add_line(line)

                    # Annotate all y-values except the first one
                    for j, y_value in enumerate(ene_array[i]):
                        if j == 0:
                            continue  # Skip the first y-value
                        x_position = j + 1  # x-positions start at 1

                        # if j is even, it is likekly a product state, if odd, it is likely a transiton state
                        if j%2==0:
                            if self.reaction:
                                self.ax.text(x_position, y_value, f'{y_value:.2f}',  # Format to 2 decimal places
                                            va='bottom', ha='center', color='black')  # Text in black
                        else:
                            if self.activation:
                                self.ax.text(x_position, y_value, f'{y_value:.2f}',  # Format to 2 decimal places
                                            va='bottom', ha='center', color='black')
                            

            except TypeError:
                pass

        return plots, legend_elements

    def plot_energy_diagram(self, ene_array=None, new_plot=True):
        """
        :param ene_array: list of lists with energies to plot as energy diagram
        :new_plot: Make new plot, instead of updating existing
        """
        if not ene_array:
            ene_array = self.ene_array

        if not new_plot:
            self.ax.clear()

        # Get Line2D energy diagrams (plots) and labels (legends)
        plots, legend_elements = self.make_energy_diagram(ene_array)

        # Get bounds for X- and Y- axes:
        x_min, x_max, y_min, y_max = self.get_bounds(ene_array)

        # Make integer X-ticks only for number of included states:
        if x_max < 9:
            self.ax.set_xticks(np.arange(1, x_max, step=1))

        # Add custom legend:
        if self.plot_legend:
            self.ax.legend(handles=legend_elements, loc="upper right")
            # Add one more tick to make space for custom legend:
            x_max += 1

        num_energies = max(len(ene) for ene in ene_array)

        # Set the positions and labels for the x-ticks
        if self.custom_names and (num_energies == len(self.custom_names)):
            self.ax.set_xticks(range(1, num_energies + 1))
            self.ax.set_xticklabels(self.custom_names)

        # Set boundary of X- and Y-axes
        y_padding = (y_max - y_min) * 0.05  # 5% of the y-range as padding, adjust as needed
        y_min_padded = y_min - y_padding  # Apply padding below the minimum y-value
        y_max_padded = y_max + y_padding  # Apply padding above the maximum y-value

        self.ax.set_ybound([y_min_padded, y_max_padded])

        # Calculate padding based on the number of energy levels
        padding = 0.5  # You can adjust this value as needed
        x_min_padded = 1 - padding  # Apply padding to the left of the first x-value
        x_max_padded = num_energies + padding  # Apply padding to the right of the last x-value

        # distribute x-ticks evenly:
        self.ax.set_xbound([x_min_padded, x_max_padded])

        for i in range(len(plots)):
            for plot in plots[i]:
                self.ax.add_artist(plot)

        if self.plot_title:
            self.ax.set_title(self.plot_title)
        if self.y_title:
            self.ax.set_ylabel(self.y_title)
        if self.x_title:
            self.ax.set_xlabel(self.x_title)
            

        if new_plot:
            self.update_style(ax=self.ax, fig=self.fig, title=self.plot_title)
            plt.show()

        else:
            plt.draw()

    def update_plot(self, ene_array, legends=None, x_title=None, y_title=None, plot_title=None, plot_legend=False,
                 line_colors=None, react_style=True):
        """
        Update existing plot
        :param ene_array:
        :param legends:
        :param x_title:
        :param y_title:
        :param plot_title:
        :param plot_legend:
        :param line_colors:
        :param react_style:
        :return:
        """
        self.x_title = x_title
        self.y_title = y_title
        self.plot_title = plot_title
        self.plot_legend = plot_legend
        self.legends = legends
        self.line_colors = line_colors

        self.set_plot_settings(react_style)
        self.update_style(ax=self.ax, fig=self.fig, title=self.plot_title)

        ene_array = self.check_array(ene_array)

        self.plot_energy_diagram(ene_array, new_plot=False)


class PlotGdata(PlotStuff):
    def __init__(self, parent=None, g_data=None, filename=None):
        super().__init__()
        self.g_data = g_data
        self.filename = filename

        # sync to pymol:
        self.pymol = None
        if parent and parent.pymol:
            self.pymol = parent.pymol

        self.fig = plt.figure()

    def plot_scf_done(self):
        """
        Creates single plot with SCF Done energies
        :return:
        """

        scf_data1 = self.fig.add_subplot(1, 1, 1)
        scf_data1.set_title("Energy")
        scf_data1.plot(list(range(1, len(self.g_data["SCF Done"]) + 1)), self.g_data["SCF Done"], label="SCF")

        plt.legend()
        plt.show()

    def plot_scf_convergence(self):
        """
        Plots SCF energy, Force and displacement from optimisation.
        :return:
        """

        self.points = list()
        #self.tmp_points = list()

        scf_data = self.fig.add_subplot(2, 4, (1, 6))
        scf_data.set_title("Energy")
        scf_data.set_ylabel("Hartree")
        scf_data.plot(list(range(1, len(self.g_data["SCF Done"])+1)), self.g_data["SCF Done"], label="SCF", picker=True)
        plt.legend()

        force = self.fig.add_subplot(2,4,(3,4))
        force.set_title("Force")
        force.set_ylabel("Hartree/Bohr")
        force.plot(list(range(1, len(self.g_data["Maximum Force"])+1)), self.g_data["Maximum Force"], label="Maximum",
                   picker=True)
        force.plot(list(range(1, len(self.g_data["RMS     Force"])+1)), self.g_data["RMS     Force"], label="RMS",
                   picker=True)
        plt.legend()

        displ = self.fig.add_subplot(2,4,(7,8))
        displ.set_title("Displacement")
        displ.set_ylabel("Angstrom")
        displ.plot(list(range(1, len(self.g_data["Maximum Displacement"])+1)),
                   self.g_data["Maximum Displacement"], label="Maximum", picker=True)
        displ.plot(list(range(1, len(self.g_data["RMS     Displacement"])+1)),
                   self.g_data["RMS     Displacement"], label="RMS", picker=True)

        plt.legend()

        self.fig.suptitle(self.filename)

        def on_pick(event):
            delete_points(self.points)
            ind = event.ind[0]

            if self.pymol:
                self.pymol.pymol_cmd("frame %s" % str(ind + 1))

            print("energy (%d) = %f" % (ind +1, self.g_data["SCF Done"][ind]))
            draw_point(ind, self.points, color="white")

        #def on_hover(event):
        #    delete_points(self.tmp_points)
        #    for curve in scf_data.get_lines():
        #        if curve.contains(event)[0]:
                    #ind = curve.contains(event)[1]['ind'][0]
        #            ind = int(event.xdata) - 1
        #            print(ind)
        #            print(event.xdata)
        #            draw_point(ind, self.tmp_points, color="blue")

        def delete_points(points):
            if len(points) > 0:
                for point in points:
                    point.remove()
                del points[:]
                plt.draw()

        def draw_point(ind, points, color="white"):

            points.append(scf_data.plot(ind + 1, self.g_data["SCF Done"][ind], "o", color=color,
                                             fillstyle='none')[0])
            points.append(force.plot(ind + 1, self.g_data["Maximum Force"][ind], "o", color=color,
                                          fillstyle='none')[0])
            points.append(force.plot(ind + 1, self.g_data["RMS     Force"][ind], "o", color=color,
                                          fillstyle='none')[0])
            points.append(displ.plot(ind + 1, self.g_data["Maximum Displacement"][ind], "o", color=color,
                                          fillstyle='none')[0])
            points.append(displ.plot(ind + 1, self.g_data["RMS     Displacement"][ind], "o", color=color,
                                          fillstyle='none')[0])
            plt.draw()

        self.fig.canvas.mpl_connect("pick_event", on_pick)
        #self.fig.canvas.mpl_connect("motion_notify_event", on_hover)

        plt.show()





