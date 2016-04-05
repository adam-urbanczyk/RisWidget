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
// Authors: Erik Hvatum <ice.rikh@gmail.com

#pragma once
#ifdef _DEBUG
 #undef _DEBUG
 #include <Python.h>
 #define _DEBUG
#else
 #include <Python.h>
#include <atomic>
#include <QtCore>
#endif

class _CppImage
  : public QObject
{
public:
    enum Status
    {
        Empty,
        AsyncLoading,
        AsyncLoadingFailed,
        Valid
    };
    enum SetFlag
    {
        SetData = 1,
        SetMask = 2,
        SetIsTwelveBit = 4,
        SetImposedFloatRange = 8,
        SetTitle = 16
    };
    Q_DECLARE_FLAGS(SetFlags, SetFlag)

private:
    Q_OBJECT
    Q_ENUM(Status)
    Q_FLAG(SetFlags)
    Q_PROPERTY(QString title READ objectName WRITE setObjectName NOTIFY title_changed FINAL)
    Q_PROPERTY(Status status READ get_status NOTIFY status_changed FINAL)
    Q_PROPERTY(std::uint64_t data_serial READ get_data_serial NOTIFY data_serial_changed FINAL)
    Q_PROPERTY(std::uint64_t mask_serial READ get_mask_serial NOTIFY mask_serial_changed FINAL)

public:
    explicit _CppImage(const QString& title=QString(), QObject* parent=nullptr);
    virtual ~_CppImage();

    QString get_title() const;
    void set_title(const QString& title);
    const Status& get_status() const;
    bool get_is_valid() const;
    const quint64& get_data_serial() const;
    const quint64& get_mask_serial() const;

//  void set(
//     SetFlags setFlags,
//     PyObject* )

signals:
    void title_changed(_CppImage*);
    void status_changed(_CppImage*);
    void is_valid_changed(_CppImage*);
    void data_serial_changed(_CppImage*);
    void mask_serial_changed(_CppImage*);

protected:
    static volatile std::atomic<quint64> sm_next_serial;
    static quint64 generate_serial();

    Status m_status;
    quint64 m_data_serial;
    quint64 m_mask_serial;
};

Q_DECLARE_OPERATORS_FOR_FLAGS(_CppImage::SetFlags)