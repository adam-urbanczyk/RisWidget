// The MIT License (MIT)
//
// Copyright (c) 2016 WUSTL ZPLAB
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Authors: Erik Hvatum <ice.rikh@gmail.com>

#include "statses.h"

template<typename T>
void StatsBase<T>::expose_via_pybind11(py::module& m)
{
    std::string s = std::string("_StatsBase_") + component_type_names[std::type_index(typeid(T))];
    py::class_<StatsBase<T>, std::shared_ptr<StatsBase<T>>>(m, s.c_str())
        .def_readonly("extrema", &StatsBase<T>::extrema)
        .def_readonly("max_bin", &StatsBase<T>::max_bin)
        .def_readonly("histogram_buff", &StatsBase<T>::histogram)
        .def_property_readonly("histogram", [](StatsBase<T>& v){return v.get_histogram_py();})
        .def("__repr__", &StatsBase<T>::operator std::string);
}

template<typename T>
StatsBase<T>::StatsBase()
  : extrema(0, 0),
    max_bin(0),
    histogram(new std::vector<std::uint64_t>()),
    histogram_py(nullptr)
{
}

template<typename T>
StatsBase<T>::operator std::string () const
{
    std::ostringstream o;
    o << "<extrema: (";
    if(std::is_same<T, char>::value || std::is_same<T, unsigned char>::value)
    {
        o << static_cast<int>(extrema.first) << ", " << static_cast<int>(extrema.second) << "), max_bin: " << max_bin;
        o << ", histogram:\n[";
        bool first{true};
        for(int v : *histogram)
        {
            if(first) first=false;
            else o << ", ";
            o << v;
        }
    }
    else
    {
        o << extrema.first << ", " << extrema.second << "), max_bin: " << max_bin;
        o << ", histogram: [";
        bool first{true};
        for(auto v : *histogram)
        {
            if(first) first=false;
            else o << ", ";
            o << v;
        }
    }
    o << "]>";
    return o.str();
}

template<typename T>
py::object& StatsBase<T>::get_histogram_py()
{
    if(!histogram_py)
    {
        py::object buffer_obj = py::cast(histogram);
        histogram_py.reset(new py::object(PyArray_FromAny(buffer_obj.ptr(), nullptr, 1, 1, 0, nullptr), false), &safe_py_deleter);
    }
    return *histogram_py;
}

template<typename T>
void StatsBase<T>::set_bin_count(std::size_t bin_count)
{
    histogram->resize(bin_count, 0);
}

template<typename T>
void StatsBase<T>::find_max_bin()
{
    const std::uint64_t* h{histogram->data()};
    max_bin = std::max_element(h, h+histogram->size()) - h;
}

template<typename T>
void FloatStatsBase<T>::expose_via_pybind11(py::module& m)
{
    StatsBase<T>::expose_via_pybind11(m);
    std::string s = std::string("_FloatStatsBase_") + component_type_names[std::type_index(typeid(T))];
    py::class_<FloatStatsBase<T>, std::shared_ptr<FloatStatsBase<T>>, StatsBase<T>>(m, s.c_str())
        .def_readonly("NaN_count", &FloatStatsBase<T>::NaN_count)
        .def_readonly("neg_inf_count", &FloatStatsBase<T>::neg_inf_count)
        .def_readonly("pos_inf_count", &FloatStatsBase<T>::pos_inf_count)
        .def("__repr__", &FloatStatsBase<T>::operator std::string);
}

template<typename T>
FloatStatsBase<T>::FloatStatsBase()
  : NaN_count(0),
    neg_inf_count(0),
    pos_inf_count(0)
{
    this->extrema.second = this->extrema.first = std::nan("");
}

template<typename T>
FloatStatsBase<T>::operator std::string () const
{
    std::string ps{StatsBase<T>::operator std::string()};
    std::ostringstream o(ps.substr(0, ps.size() - 2));
    o << "NaN_count: " << NaN_count << ", neg_inf_count: " << neg_inf_count << ", pos_inf_count: " << pos_inf_count << ">";
    return o.str();
}

// Note that concrete specializations of this function for T=float and T=double are found in statses.cpp
template<typename T>
void Stats<T>::expose_via_pybind11(py::module& m)
{
    StatsBase<T>::expose_via_pybind11(m);
    std::string s = std::string("_Stats_") + component_type_names[std::type_index(typeid(T))];
    py::class_<Stats<T>, std::shared_ptr<Stats<T>>, StatsBase<T>>(m, s.c_str());
}

template<typename T>
void ImageStats<T>::expose_via_pybind11(py::module& m)
{
    Stats<T>::expose_via_pybind11(m);
    std::string s = std::string("_ImageStats_") + component_type_names[std::type_index(typeid(T))];
    py::class_<ImageStats<T>, std::shared_ptr<ImageStats<T>>>(m, s.c_str())
        .def_readonly("channel_stats", &ImageStats<T>::channel_stats)
        .def("__repr__", &ImageStats<T>::operator std::string);
    s = std::string("_Stats_") + component_type_names[std::type_index(typeid(T))] + "_list";
    py::bind_vector<std::vector<std::shared_ptr<Stats<T>>>>(m, s);
}

template<typename T>
ImageStats<T>::operator std::string () const
{
    std::string ps{};
    std::ostringstream o;
    if(channel_stats.size() == 1)
    {
        o << Stats<T>::operator std::string();
    }
    else
    {
        o << "<Overall: " << Stats<T>::operator std::string();
        for(typename decltype(channel_stats)::const_iterator cs{channel_stats.cbegin()}; cs != channel_stats.end(); ++cs)
        {
            o << ",\nChannel " << (cs - channel_stats.cbegin()) << ": " << static_cast<std::string>(**cs);
        }
    }
    o << '>';
    return o.str();
}

template<typename T>
void ImageStats<T>::set_bin_count(std::size_t bin_count)
{
    Stats<T>::set_bin_count(bin_count);
    for(std::shared_ptr<Stats<T>>& channel_stat : channel_stats)
        channel_stat->set_bin_count(bin_count);
}